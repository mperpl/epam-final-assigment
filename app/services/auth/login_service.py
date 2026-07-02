from fastapi import Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from valkey.asyncio import Valkey

from app.api.schemas.dto.user import UserLoginDTO
from app.core.exceptions import AuthenticationError
from app.core.security import (
    create_access_token,
    create_refresh_token,
    create_token_cookie,
    verify_password,
)
from app.models.user import User


async def login_service(
    response: Response, login_data: UserLoginDTO, db: AsyncSession, valkey: Valkey
) -> User:
    stmt = select(User).where(User.email == login_data.email)
    user = (await db.execute(stmt)).scalar_one_or_none()

    if not user or not await verify_password(
        login_data.password.get_secret_value(), user.password
    ):
        raise AuthenticationError("Incorrect email or password.")

    access_token = create_access_token({"sub": str(user.id)})
    create_token_cookie(response, access_token, is_refresh=False)

    refresh_token = await create_refresh_token({"sub": str(user.id)}, valkey)
    create_token_cookie(response, refresh_token, is_refresh=True)

    return user
