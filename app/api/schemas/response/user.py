from uuid import UUID

from pydantic import BaseModel, EmailStr

from app.api.schemas.from_attributes_true import BaseResponseModel


class UserRegistrationResponse(BaseResponseModel):
    id: UUID
    email: EmailStr
    message: str = "User registered successfully."

class UserLoginResponse(BaseResponseModel):
    id: UUID
    email: EmailStr
    message: str = "Login successful."

class CurrentUserResponse(BaseResponseModel):
    id: UUID
    email: EmailStr
    message: str = "Profile data retrived successfully."

class UserLogoutResponse(BaseModel):
    message: str = "Logged out successfully from current session."

class UserLogoutAllResponse(BaseModel):
    message: str = "Logged out successfully from all active sessions."

class UserRefreshResponse(BaseModel):
    message: str = "Session token renewed successfully."