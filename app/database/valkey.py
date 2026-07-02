from datetime import timedelta
from typing import Annotated, AsyncGenerator

from fastapi import Depends, Request
from valkey.asyncio import Valkey


async def get_valkey(request: Request) -> AsyncGenerator[Valkey, None]:
    pool = request.app.state.valkey_pool
    client = Valkey.from_pool(pool)
    try:
        yield client
    finally:
        await client.aclose()

VALKEY_CLIENT = Annotated[Valkey, Depends(get_valkey)]

def generate_valkey_session_string(user_id: str, refresh_token_jti: str):
    return f"user_id:{user_id}:refresh_token_jti:{refresh_token_jti}"

async def set_valkey_session(user_id: str, refresh_token_jti: str, timedelta: timedelta, valkey: Valkey):
    key = generate_valkey_session_string(user_id, refresh_token_jti)
    await valkey.setex(key, timedelta, '1')

async def get_valkey_session(user_id: str, refresh_token_jti: str, valkey: Valkey):
    key = generate_valkey_session_string(user_id, refresh_token_jti)
    return await valkey.get(key)

async def delete_valkey_session(user_id: str, refresh_token_jti: str, valkey: Valkey) -> None:
    old_key = generate_valkey_session_string(user_id, refresh_token_jti)
    await valkey.delete(old_key)
    
async def delete_valkey_sessions(user_id: str, valkey: Valkey):
    pattern = f"user_id:{user_id}:refresh_token_jti:*"
    keys_to_delete = []
    async for key in valkey.scan_iter(match=pattern):
        keys_to_delete.append(key)

    if keys_to_delete:
        await valkey.delete(*keys_to_delete)
