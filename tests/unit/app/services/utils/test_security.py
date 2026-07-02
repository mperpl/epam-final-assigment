from unittest.mock import ANY, AsyncMock, patch
from uuid import uuid4

import jwt
import pytest

from app.core.exceptions import (
    AuthenticationError,
    AuthorizationError,
    DatabaseIntegrityError,
    EntryNotFoundError,
)
from app.core.settings import settings
from app.models.project_member import ProjectRole
from app.services.utils.security import (
    get_credentials_from_refresh_token,
    protect_owner_deletion,
    user_role_in,
)


class TestProtectOwnerDeletion:
    @pytest.mark.asyncio
    @patch("app.services.utils.security.get_project_member", new_callable=AsyncMock)
    async def test_protect_owner_deletion_success_case_a(self, mock_get_member):
        """Case A: Current user is the owner and target is a different user; passes silently."""
        mock_db = AsyncMock()
        
        # Mocking the returned member to be an OWNER
        mock_member = AsyncMock()
        mock_member.role = ProjectRole.OWNER
        mock_get_member.return_value = mock_member
        
        current_user = uuid4()
        target_user = uuid4()  # Distinct user ID
        
        await protect_owner_deletion(
            current_user_id=current_user,
            target_user_id=target_user,
            project_id=uuid4(),
            db=mock_db
        )
        mock_get_member.assert_called_once_with(current_user, ANY, mock_db)

    @pytest.mark.asyncio
    @patch("app.services.utils.security.get_project_member", new_callable=AsyncMock)
    async def test_protect_owner_deletion_denied_case_b(self, mock_get_member):
        """Case B: Current user is an EDITOR, not the OWNER; raises AuthorizationError."""
        mock_db = AsyncMock()
        
        # Mocking the returned member to be an EDITOR
        mock_member = AsyncMock()
        mock_member.role = ProjectRole.EDITOR
        mock_get_member.return_value = mock_member
        
        with pytest.raises(AuthorizationError) as exc_info:
            await protect_owner_deletion(
                current_user_id=uuid4(),
                target_user_id=uuid4(),
                project_id=uuid4(),
                db=mock_db
            )
            
        assert str(exc_info.value) == "Access denied. Only the project owner can alter member roles."

    @pytest.mark.asyncio
    @patch("app.services.utils.security.get_project_member", new_callable=AsyncMock)
    async def test_protect_owner_deletion_self_conflict_case_c(self, mock_get_member):
        """Case C: Current user is OWNER but targets themselves; raises DatabaseIntegrityError."""
        mock_db = AsyncMock()
        
        # Mocking the returned member to be an OWNER
        mock_member = AsyncMock()
        mock_member.role = ProjectRole.OWNER
        mock_get_member.return_value = mock_member
        
        same_user_id = uuid4()
        
        with pytest.raises(DatabaseIntegrityError) as exc_info:
            await protect_owner_deletion(
                current_user_id=same_user_id,
                target_user_id=same_user_id,  # Conflict trigger
                project_id=uuid4(),
                db=mock_db
            )
            
        assert str(exc_info.value) == "Safety conflict: You cannot modify your own ownership role."


class TestGetCredentialsFromRefreshToken:
    @pytest.mark.asyncio
    @patch("app.services.utils.security.get_valkey_session", new_callable=AsyncMock)
    async def test_get_credentials_success_case_a(self, mock_get_session):
        """Case A: Clean extraction when Valkey returns valid session string data."""
        mock_valkey = AsyncMock()
        
        mock_get_session.return_value = "whatever" 
        
        payload = {"sub": "user-uuid-123", "jti": "jti-uuid-456"}
        valid_token = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        
        user_id, jti = await get_credentials_from_refresh_token(valid_token, mock_valkey)
        
        assert user_id == "user-uuid-123"
        assert jti == "jti-uuid-456"
        mock_get_session.assert_called_once_with("user-uuid-123", "jti-uuid-456", mock_valkey)

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "bad_payload",
        [
            {"sub": "user-uuid-123"},  # Missing jti
            {"jti": "jti-uuid-456"},  # Missing sub
            {},                        # Missing both
        ]
    )
    async def test_get_credentials_malformed_metadata_case_b(self, bad_payload):
        """Case B: Missing critical fields in token payload triggers AuthenticationError."""
        mock_valkey = AsyncMock()
        invalid_token = jwt.encode(bad_payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        
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
        valid_token = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        
        with pytest.raises(AuthenticationError) as exc_info:
            await get_credentials_from_refresh_token(valid_token, mock_valkey)
            
        assert str(exc_info.value) == "Refresh token revoked or expired."
        

class TestUserRoleIn:
    @pytest.mark.asyncio
    @patch("app.services.utils.security.get_project_member", new_callable=AsyncMock)
    async def test_user_role_in_success_case_a(self, mock_get_member):
        """Case A: Returns True when the user has an explicit allowed role."""
        mock_db = AsyncMock()
        
        # Mock a valid member with an allowed role
        mock_member = AsyncMock()
        mock_member.role = ProjectRole.EDITOR
        mock_get_member.return_value = mock_member

        result = await user_role_in(
            project_id=uuid4(),
            user_id=uuid4(),
            roles=(ProjectRole.OWNER, ProjectRole.EDITOR),
            db=mock_db
        )

        assert result is True
        mock_get_member.assert_called_once()

    @pytest.mark.asyncio
    @patch("app.services.utils.security.get_project_member", new_callable=AsyncMock)
    async def test_user_role_in_forbidden_role_case_b(self, mock_get_member):
        """Case B: Raises AuthorizationError if user has a role, but it's not allowed."""
        mock_db = AsyncMock()
        
        # Mock a valid member but with a forbidden role for this action
        mock_member = AsyncMock()
        mock_member.role = ProjectRole.VIEWER
        mock_get_member.return_value = mock_member

        with pytest.raises(AuthorizationError) as exc_info:
            await user_role_in(
                project_id=uuid4(),
                user_id=uuid4(),
                roles=(ProjectRole.OWNER, ProjectRole.EDITOR),
                db=mock_db
            )

        assert str(exc_info.value) == "User has no access to this action"

    @pytest.mark.asyncio
    @patch("app.services.utils.security.get_project_member", new_callable=AsyncMock)
    async def test_user_role_in_stranger_non_member_case_c(self, mock_get_member):
        """Case C: Catches EntryNotFoundError safely and still raises AuthorizationError."""
        mock_db = AsyncMock()
        
        # Force the query utility to throw a 404 mapping error
        mock_get_member.side_effect = EntryNotFoundError("Target user is not currently a member...")

        with pytest.raises(AuthorizationError) as exc_info:
            await user_role_in(
                project_id=uuid4(),
                user_id=uuid4(),
                roles=(ProjectRole.OWNER, ProjectRole.EDITOR),
                db=mock_db
            )

        # Ensures we leak a 403 Forbidden error, masking the database's 404 state completely!
        assert str(exc_info.value) == "User has no access to this action"