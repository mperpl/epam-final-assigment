from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from valkey.asyncio import Valkey

from app.core.exceptions import (
    AuthenticationError,
    AuthorizationError,
    EntryNotFoundError,
)
from app.core.security import decode_jwt
from app.database.queries.project_member import get_project_member
from app.database.valkey import get_valkey_session
from app.models.project_member import ProjectRole


def protect_owner_deletion(current_user_id: UUID, target_user_id: UUID) -> None:
    if current_user_id == target_user_id:
        raise AuthorizationError(
            "Safety conflict: You cannot modify your own ownership role."
        )
    


async def get_credentials_from_refresh_token(
    refresh_token: str, valkey: Valkey
) -> tuple[str, str]:
    decoded_refresh_token = decode_jwt(refresh_token)
    refresh_token_jti = decoded_refresh_token.get("jti")
    user_id = decoded_refresh_token.get("sub")

    if not refresh_token_jti or not user_id:
        raise AuthenticationError("Malformed token metadata payloads detected.")

    key_exists = await get_valkey_session(user_id, refresh_token_jti, valkey)
    if not key_exists:
        raise AuthenticationError("Refresh token revoked or expired.")

    return user_id, refresh_token_jti


async def user_role_in(
    project_id: UUID, user_id: UUID, roles: tuple[ProjectRole | None], db: AsyncSession
) -> bool:
    try:
        member = await get_project_member(user_id, project_id, db)
    except EntryNotFoundError:
        raise AuthorizationError("User has no access to this action.")
    
    if member.role in roles:
        return True
    
    raise AuthorizationError("User has no access to this action.")
