from fastapi import APIRouter, Cookie, Request, Response, status

from app.api.dependencies.auth import CURRENT_USER, CURRENT_USER_ID, LOGGED_OUT_GUARD
from app.api.schemas.dto.user import UserLoginDTO, UserRegisterDTO
from app.api.schemas.response.user import (
    CurrentUserResponse,
    UserLoginResponse,
    UserLogoutAllResponse,
    UserLogoutResponse,
    UserRefreshResponse,
    UserRegistrationResponse,
)
from app.database.sql_db import DB_SESSION
from app.database.valkey import VALKEY_CLIENT
from app.services.auth.login_service import login_service
from app.services.auth.logout_all_service import logout_all_service
from app.services.auth.logout_service import logout_service
from app.services.auth.refresh_service import refresh_service
from app.services.auth.register_service import register_service

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/register",
    status_code=status.HTTP_201_CREATED,
    response_model=UserRegistrationResponse,
)
async def register(register_data: UserRegisterDTO, db: DB_SESSION, _: LOGGED_OUT_GUARD):
    return await register_service(register_data, db)


@router.post("/login", status_code=status.HTTP_200_OK, response_model=UserLoginResponse)
async def login(
    response: Response,
    login_data: UserLoginDTO,
    db: DB_SESSION,
    valkey: VALKEY_CLIENT,
    _: LOGGED_OUT_GUARD,
):
    return await login_service(response, login_data, db, valkey)


@router.post(
    "/logout", status_code=status.HTTP_200_OK, response_model=UserLogoutResponse
)
async def logout(
    response: Response,
    request: Request,
    valkey: VALKEY_CLIENT,
    user_id: CURRENT_USER_ID,
):
    await logout_service(response, request, valkey, user_id)
    return {}


@router.post(
    "/logout-all", status_code=status.HTTP_200_OK, response_model=UserLogoutAllResponse
)
async def logout_all(
    response: Response, valkey: VALKEY_CLIENT, user_id: CURRENT_USER_ID
):
    await logout_all_service(response, valkey, user_id)
    return {}


@router.post(
    "/refresh", status_code=status.HTTP_200_OK, response_model=UserRefreshResponse
)
async def refresh(
    response: Response, valkey: VALKEY_CLIENT, refresh_token: str = Cookie()
):
    await refresh_service(response, refresh_token, valkey)
    return {}


@router.get("/me", status_code=status.HTTP_200_OK, response_model=CurrentUserResponse)
async def current_user(current_user: CURRENT_USER):
    return current_user
