from uuid import UUID

import pytest
from fastapi import status
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User


@pytest.mark.asyncio
async def test_register_user_success(client: AsyncClient, db_session: AsyncSession):
    """Verifies that a user can register successfully."""
    registration_payload = {
        "email": "testuser_2026@example.com",
        "password1": "SecurePassword123!",
        "password2": "SecurePassword123!",
    }
    response = await client.post("/auth/register", json=registration_payload)
    assert response.status_code == status.HTTP_201_CREATED

    stmt = select(User).where(User.email == "testuser_2026@example.com")
    db_user = (await db_session.execute(stmt)).scalar_one_or_none()
    assert db_user is not None


@pytest.mark.asyncio
async def test_register_user_password_mismatch_fails(client: AsyncClient):
    """Verifies that Pydantic drops the request with a 422 if passwords don't match."""
    mismatched_payload = {
        "email": "mismatch_2026@example.com",
        "password1": "SecurePassword123!",
        "password2": "CompletelyDifferentPassword99!",
    }
    response = await client.post("/auth/register", json=mismatched_payload)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


@pytest.mark.parametrize(
    "bad_email",
    [
        "plainstring",  # Missing @ and domain
        "@missing-local.com",  # Missing local mailbox part
        "test@com",  # Missing top-level domain extension mapping structure
        "spaces in@email.com",  # Illegal whitespace characters
    ],
)
@pytest.mark.asyncio
async def test_register_invalid_email_formats_fail(client: AsyncClient, bad_email: str):
    """Verifies that Pydantic rejects structurally broken email inputs with a 422 error."""
    payload = {
        "email": bad_email,
        "password1": "SecurePassword123!",
        "password2": "SecurePassword123!",
    }
    response = await client.post("/auth/register", json=payload)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


@pytest.mark.parametrize(
    "incomplete_payload",
    [
        {
            "password1": "Pass123!",
            "password2": "Pass123!",
        },  # Missing email key entirely
        {
            "email": "",
            "password1": "Pass123!",
            "password2": "Pass123!",
        },  # Empty email string
        {
            "email": "valid@test.com",
            "password1": "",
            "password2": "Pass123!",
        },  # Empty password
    ],
)
@pytest.mark.asyncio
async def test_register_empty_or_missing_fields_fail(
    client: AsyncClient, incomplete_payload: dict
):
    """Verifies that missing keys or empty strings for required arguments trigger a 422."""
    response = await client.post("/auth/register", json=incomplete_payload)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


@pytest.mark.asyncio
async def test_register_user_duplicate_email_fails(
    client: AsyncClient, db_session: AsyncSession, test_user_id: UUID
):
    """Verifies that registering an existing email handles the database conflict safely."""
    existing_user = User(
        id=test_user_id, email="duplicate@example.com", password="hashed_placeholder"
    )
    db_session.add(existing_user)
    await db_session.commit()

    duplicate_payload = {
        "email": "duplicate@example.com",
        "password1": "DifferentPassword99!",
        "password2": "DifferentPassword99!",
    }
    response = await client.post("/auth/register", json=duplicate_payload)
    assert response.status_code in [
        status.HTTP_400_BAD_REQUEST,
        status.HTTP_409_CONFLICT,
    ]
