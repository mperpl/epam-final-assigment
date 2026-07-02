from uuid import UUID

from fastapi import Request, Response
from valkey.asyncio import Valkey

from app.core.security import decode_jwt, delete_token_cookie
from app.database.valkey import delete_valkey_session


async def logout_service(response: Response, request: Request, valkey: Valkey, user_id: UUID) -> None:
    refresh_token = request.cookies.get("refresh_token")
    if refresh_token:
        jti = decode_jwt(refresh_token).get('jti')
        await delete_valkey_session(str(user_id), jti, valkey)

    delete_token_cookie(response, is_refresh=False)
    delete_token_cookie(response, is_refresh=True)
