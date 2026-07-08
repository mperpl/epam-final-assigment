from unittest.mock import AsyncMock, patch
from uuid import uuid4

import jwt
import pytest

from app.core.exceptions import (
    AuthenticationError,
    AuthorizationError,
    EntryNotFoundError,
)
from app.core.settings import settings
from app.models.project_member import ProjectMember, ProjectRole
from app.services.utils.security import (
    get_credentials_from_refresh_token,
    protect_owner_deletion,
    user_role_in,
)


class TestProtectOwnerDeletion:
    def test_protect_owner_deletion_success_case_a(self):
        """Case A: Current user is the owner and target is a different user; passes silently."""

        current_user = uuid4()
        target_user = uuid4()  # Distinct user ID

        protect_owner_deletion(
            current_user_id=current_user,
            target_user_id=target_user
        )


    def test_protect_owner_deletion_self_conflict_case_b(self):
        """Case C: Current user is OWNER but targets themselves; raises DatabaseIntegrityError."""
        same_user_id = uuid4()

        with pytest.raises(AuthorizationError) as exc_info:
            protect_owner_deletion(
                current_user_id=same_user_id,
                target_user_id=same_user_id  # Conflict trigger
            )

        assert (
            str(exc_info.value)
            == "Safety conflict: You cannot modify your own ownership role."
        )


class TestGetCredentialsFromRefreshToken:
    @pytest.mark.asyncio
    @patch("app.services.utils.security.get_valkey_session", new_callable=AsyncMock)
    async def test_get_credentials_success_case_a(self, mock_get_session):
        """Case A: Clean extraction when Valkey returns valid session string data."""
        mock_valkey = AsyncMock()

        mock_get_session.return_value = "whatever"

        payload = {"sub": "user-uuid-123", "jti": "jti-uuid-456"}
        valid_token = jwt.encode(
            payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM
        )

        user_id, jti = await get_credentials_from_refresh_token(
            valid_token, mock_valkey
        )

        assert user_id == "user-uuid-123"
        assert jti == "jti-uuid-456"
        mock_get_session.assert_called_once_with(
            "user-uuid-123", "jti-uuid-456", mock_valkey
        )

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "bad_payload",
        [
            {"sub": "user-uuid-123"},  # Missing jti
            {"jti": "jti-uuid-456"},  # Missing sub
            {},  # Missing both
        ],
    )
    async def test_get_credentials_malformed_metadata_case_b(self, bad_payload):
        """Case B: Missing critical fields in token payload triggers AuthenticationError."""
        mock_valkey = AsyncMock()
        invalid_token = jwt.encode(
            bad_payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM
        )

        with pytest.raises(AuthenticationError) as exc_info:
            await get_credentials_from_refresh_token(invalid_token, mock_valkey)

        assert str(exc_info.value) == "Malformed token metadata payloads detected."

    @pytest.mark.asyncio
    @patch("app.services.utils.security.get_valkey_session", new_callable=AsyncMock)
    async def test_get_credentials_revoked_session_case_c(self, mock_get_session):
        """Case C: Valid token structure but Valkey returns None (expired/revoked)."""
        mock_valkey = AsyncMock()

        mock_get_session.return_value = None

        payload = {"sub": "user-uuid-789", "jti": "jti-uuid-000"}
        valid_token = jwt.encode(
            payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM
        )

        with pytest.raises(AuthenticationError) as exc_info:
            await get_credentials_from_refresh_token(valid_token, mock_valkey)

        assert str(exc_info.value) == "Refresh token revoked or expired."


class TestUserRoleIn:
    @pytest.mark.asyncio
    @patch("app.services.utils.security.get_project_member", new_callable=AsyncMock)
    async def test_user_role_in_success_case_a(self, mock_get_member):
        """Case A: Returns True when the user has an explicit allowed role."""
        mock_db = AsyncMock()

        real_member = ProjectMember(role=ProjectRole.EDITOR)
        mock_get_member.return_value = real_member

        result = await user_role_in(
            project_id=uuid4(),
            user_id=uuid4(),
            roles=(ProjectRole.OWNER, ProjectRole.EDITOR),
            db=mock_db,
        )

        assert result is True
        mock_get_member.assert_called_once()

    @pytest.mark.asyncio
    @patch("app.services.utils.security.get_project_member", new_callable=AsyncMock)
    async def test_user_role_in_forbidden_role_case_b(self, mock_get_member):
        """Case B: Raises AuthorizationError if user has a role, but it's not allowed."""
        mock_db = AsyncMock()

        real_member = ProjectMember(role=ProjectRole.VIEWER)
        mock_get_member.return_value = real_member

        with pytest.raises(AuthorizationError) as exc_info:
            await user_role_in(
                project_id=uuid4(),
                user_id=uuid4(),
                roles=(ProjectRole.OWNER, ProjectRole.EDITOR),
                db=mock_db,
            )

        assert str(exc_info.value) == "User has no access to this action."

    @pytest.mark.asyncio
    @patch("app.services.utils.security.get_project_member", new_callable=AsyncMock)
    async def test_user_role_in_stranger_non_member_case_c(self, mock_get_member):
        """Case C: Catches EntryNotFoundError safely and still raises AuthorizationError."""
        mock_db = AsyncMock()

        # Force the query utility to throw a 404 mapping error
        mock_get_member.side_effect = EntryNotFoundError(
            "Target user is not currently a member of this project."
        )

        with pytest.raises(AuthorizationError) as exc_info:
            await user_role_in(
                project_id=uuid4(),
                user_id=uuid4(),
                roles=(ProjectRole.OWNER, ProjectRole.EDITOR),
                db=mock_db,
            )

        assert str(exc_info.value) == "User has no access to this action."
