from uuid import UUID

from fastapi import Response
from valkey.asyncio import Valkey

from app.core.security import delete_token_cookie
from app.database.valkey import delete_valkey_sessions


async def logout_all_service(response: Response, valkey: Valkey, user_id: UUID) -> None:
    await delete_valkey_sessions(str(user_id), valkey)

    delete_token_cookie(response, is_refresh=False)
    delete_token_cookie(response, is_refresh=True)


