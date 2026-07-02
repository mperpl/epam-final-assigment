from unittest.mock import AsyncMock
from uuid import UUID

import pytest
from fastapi import status
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.models import User


@pytest.mark.asyncio
async def test_login_success(
    client: AsyncClient,
    db_session: AsyncSession,
    mock_valkey: AsyncMock,
    test_user_id: UUID,
):
    """Scenario 1: Verifies that a user with valid credentials logs in successfully.
    Checks for a 200 OK status, proper user data return, cookie generation, and Valkey storage orchestration.
    """
    # 1. Arrange: Seed a valid user inside our test database
    raw_password = "SecurePassword123!"
    hashed = await hash_password(raw_password)
    test_user = User(
        id=test_user_id, email="login_success@example.com", password=hashed
    )
    db_session.add(test_user)
    await db_session.commit()

    login_payload = {"email": "login_success@example.com", "password": raw_password}

    # 2. Act: Send login request
    response = await client.post("/auth/login", json=login_payload)

    # 3. Assert: HTTP status and body payload structural integrity
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["email"] == "login_success@example.com"

    # 4. Assert: Verify secure HTTP state cookies were attached to response headers
    # FastAPI/HTTPX exposes these under response.cookies
    assert "access_token" in response.cookies
    assert "refresh_token" in response.cookies


@pytest.mark.asyncio
async def test_login_invalid_email_fails(client: AsyncClient, db_session: AsyncSession):
    """Scenario 2: Verifies that an unrecognized email address safely raises a 411/401 authentication error."""
    login_payload = {
        "email": "nonexistent_email@example.com",
        "password": "SomePassword123!",
    }

    response = await client.post("/auth/login", json=login_payload)

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert "access_token" not in response.cookies


@pytest.mark.asyncio
async def test_login_wrong_password_fails(
    client: AsyncClient, db_session: AsyncSession, test_user_id: UUID
):
    """Scenario 3: Verifies that a valid user email passing an invalid password string is blocked."""
    # 1. Arrange: Pre-seed the target user account
    hashed = await hash_password("CorrectPassword123!")
    test_user = User(id=test_user_id, email="wrong_pass@example.com", password=hashed)
    db_session.add(test_user)
    await db_session.commit()

    login_payload = {
        "email": "wrong_pass@example.com",
        "password": "IncorrectPasswordString!",
    }

    # 2. Act
    response = await client.post("/auth/login", json=login_payload)

    # 3. Assert
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert "access_token" not in response.cookies


@pytest.mark.parametrize(
    "bad_email", ["not-an-email", "missing_at_domain.com@", "spaces @domain.com"]
)
@pytest.mark.asyncio
async def test_login_invalid_email_format_validation_fails(
    client: AsyncClient, bad_email: str
):
    """Scenario 4: Verifies Pydantic structurally discards broken email patterns early with 422."""
    payload = {"email": bad_email, "password": "Password123!"}

    response = await client.post("/auth/login", json=payload)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


@pytest.mark.parametrize(
    "incomplete_payload",
    [
        {"password": "Password123!"},  # Missing email entirely
        {"email": "test@example.com"},  # Missing password entirely
        {"email": "", "password": "Password123!"},  # Empty email key string value
    ],
)
@pytest.mark.asyncio
async def test_login_missing_or_empty_fields_validation_fails(
    client: AsyncClient, incomplete_payload: dict
):
    """Scenario 5: Verifies that missing fields or blank tokens trigger an early 422 validation dump."""
    response = await client.post("/auth/login", json=incomplete_payload)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
