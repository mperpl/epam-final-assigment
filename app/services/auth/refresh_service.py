from fastapi import Response
from valkey.asyncio import Valkey

from app.core.security import (
    create_access_token,
    create_refresh_token,
    create_token_cookie,
)
from app.database.valkey import delete_valkey_session
from app.services.utils.security import get_credentials_from_refresh_token


async def refresh_service(
    response: Response, refresh_token: str, valkey: Valkey
) -> None:
    user_id, old_jti = await get_credentials_from_refresh_token(refresh_token, valkey)

    new_refresh_token = await create_refresh_token({"sub": user_id}, valkey)
    await delete_valkey_session(user_id, old_jti, valkey)
    create_token_cookie(response, new_refresh_token, is_refresh=True)

    access_token = create_access_token({"sub": user_id})
    create_token_cookie(response, access_token, is_refresh=False)
