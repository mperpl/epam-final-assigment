from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import uuid4

import jwt
from fastapi import Response
from fastapi.concurrency import run_in_threadpool
from fastapi.security import APIKeyCookie
from pwdlib import PasswordHash
from valkey.asyncio import Valkey

from app.core.exceptions import (
    AppExceptionError,
    DataIntegrityError,
    InvalidTokenSignatureError,
    TokenDecodingError,
    TokenExpiredError,
)
from app.core.settings import settings
from app.database.valkey import set_valkey_session

oauth2_cookie_scheme = APIKeyCookie(name="access_token")


def create_access_token(
    data: dict, access_token_expire_minutes: int = settings.ACCESS_TOKEN_EXPIRE_MINUTES
) -> str:
    """data argument should be filled with {'sub': user_uuid}"""
    if not data.get("sub"):
        raise DataIntegrityError("Token payload has to contain 'sub' field.")
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=access_token_expire_minutes)
    to_encode.update({"exp": expire})

    encoded_jwt = jwt.encode(
        to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
    )
    return encoded_jwt


async def create_refresh_token(
    data: dict,
    valkey: Valkey,
    refresh_token_expire_days: int = settings.REFRESH_TOKEN_EXPIRE_DAYS,
) -> str:
    """data argument should be filled with {'sub': user_uuid}"""
    if not data.get("sub"):
        raise DataIntegrityError("Token payload has to contain 'sub' field.")
    to_encode = data.copy()
    delta_exp = timedelta(days=refresh_token_expire_days)
    expire = datetime.now(timezone.utc) + delta_exp
    str_jti = str(uuid4())

    to_encode.update({"jti": str_jti})
    to_encode.update({"exp": expire})

    encoded_jwt = jwt.encode(
        to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
    )

    str_user_id = to_encode.get("sub")
    await set_valkey_session(str_user_id, str_jti, delta_exp, valkey)

    return encoded_jwt


def create_token_cookie(response: Response, token, is_refresh=False) -> None:
    response.set_cookie(
        key="refresh_token" if is_refresh else "access_token",
        value=token,
        httponly=True,
        secure=True if settings.IS_HTTPS == 'true' else False,
        samesite="lax",
        path="/",
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 86_400
        if is_refresh
        else settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


def delete_token_cookie(response: Response, is_refresh=False) -> None:
    response.delete_cookie(
        key="refresh_token" if is_refresh else "access_token",
        path="/",
        httponly=True,
        secure=True if settings.IS_HTTPS == 'true' else False,
        samesite="lax",
    )


def decode_jwt(token) -> dict[str, Any]:
    try:
        return jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
            options={"verify_exp": True, "verify_signature": True},
        )
    except jwt.ExpiredSignatureError:
        raise TokenExpiredError()
    except jwt.InvalidSignatureError:
        raise InvalidTokenSignatureError()
    except jwt.DecodeError:
        raise TokenDecodingError()
    except Exception as e:
        raise AppExceptionError(
            status_code=422,
            message=f"Encountered some issue when decoding the token: {e}",
        )


password_hash = PasswordHash.recommended()


async def hash_password(password) -> bool:
    return await run_in_threadpool(password_hash.hash, password)


async def verify_password(plain_password, hashed_password) -> bool:
    return await run_in_threadpool(
        password_hash.verify, plain_password, hashed_password
    )
