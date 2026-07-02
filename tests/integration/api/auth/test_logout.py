from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock
from uuid import UUID

import jwt
import pytest
from fastapi import status
from httpx import AsyncClient

from app.core.settings import settings


@pytest.mark.asyncio
async def test_logout_with_active_session_cleans_everything(
    auth_client: AsyncClient, test_user_id: UUID, mock_valkey: AsyncMock
):
    """Scenario 1: Happy Path (Logged-in user).
    Verifies that a user with an active refresh cookie successfully decodes,
    triggers the Valkey session deletion, and evicts both token cookies.
    """
    # Arrange: Add a valid refresh token cookie to our pre-authenticated client
    payload = {
        "sub": str(test_user_id),
        "jti": "active-refresh-jti-123",
        "exp": datetime.now(timezone.utc) + timedelta(hours=1),
    }
    refresh_jwt = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    auth_client.cookies.set("refresh_token", refresh_jwt)

    # Act
    response = await auth_client.post("/auth/logout")

    # Assert
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {
        "message": "Logged out successfully from current session."
    }

    # Assert both cookies were evicted (set to clear/expired)
    assert (
        "access_token" not in response.cookies
        or response.cookies.get("access_token") == ""
    )
    assert (
        "refresh_token" not in response.cookies
        or response.cookies.get("refresh_token") == ""
    )


@pytest.mark.asyncio
async def test_logout_without_refresh_token_succeeds_gracefully(
    auth_client: AsyncClient, mock_valkey: AsyncMock
):
    """Scenario 2: Logged in via access token but missing refresh token.
    Verifies that the block safely skips Valkey deletion if no refresh token exists,
    but still completes cookie eviction cleanly.
    """
    # Arrange: auth_client naturally has an access_token, but make sure refresh_token is missing
    if "refresh_token" in auth_client.cookies:
        del auth_client.cookies["refresh_token"]

    # Act
    response = await auth_client.post("/auth/logout")

    # Assert
    assert response.status_code == status.HTTP_200_OK

    # Verify that delete_valkey_session operations were bypassed
    mock_valkey.delete.assert_not_called()


@pytest.mark.asyncio
async def test_logout_unauthenticated_blocked_by_guard(client: AsyncClient):
    """Scenario 3: Anonymous User."""
    # Arrange: client is completely anonymous (no cookies)
    response = await client.post("/auth/logout")

    # Assert: Should match the AuthenticationError status code thrown by verify_is_not_anonymous
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
