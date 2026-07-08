from typing import Annotated
from uuid import UUID

import jwt
from fastapi import Depends, Request

from app.core.exceptions import AppExceptionError, AuthenticationError, AuthorizationError
from app.core.security import decode_jwt
from app.database.sql_db import DB_SESSION
from app.models.user import User

CREDENTIALS_EXCEPTION = AuthenticationError("Could not validate credentials.")


def has_token(request: Request) -> bool:
    return bool(request.cookies.get("access_token"))


def verify_is_anonymous(request: Request) -> None:
    has = has_token(request)
    if has:
        raise AuthorizationError("Route inaccessible for logged in users.")


def verify_is_not_anonymous(request: Request) -> None:
    has = has_token(request)
    if not has:
        raise AuthenticationError("Route inaccessible for logged out users.")


def decode_user_id_from_cookie(request: Request) -> UUID:
    token = request.cookies.get("access_token")
    if not token:
        raise CREDENTIALS_EXCEPTION
    try:
        payload = decode_jwt(token)
        id_str = payload.get("sub")

        if id_str is None:
            raise CREDENTIALS_EXCEPTION
        return UUID(id_str)
    except (AppExceptionError, jwt.InvalidTokenError):
        raise CREDENTIALS_EXCEPTION


def get_current_user_id(request: Request) -> UUID:
    return decode_user_id_from_cookie(request)


async def get_current_user(request: Request, db: DB_SESSION) -> User:
    user_id = decode_user_id_from_cookie(request)

    user = await db.get(User, user_id)
    if user is None:
        raise CREDENTIALS_EXCEPTION
    return user


CURRENT_USER_ID = Annotated[UUID, Depends(get_current_user_id)]
CURRENT_USER = Annotated[User, Depends(get_current_user)]
LOGGED_OUT_GUARD = Annotated[bool, Depends(verify_is_anonymous)]
LOGGED_IN_GUARD = Annotated[bool, Depends(verify_is_not_anonymous)]
