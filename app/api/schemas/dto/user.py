from pydantic import BaseModel, EmailStr, Field, SecretStr, model_validator
from typing_extensions import Self

from app.models.project_member import GrantProjectRole


class UserLoginDTO(BaseModel):
    email: EmailStr
    password: SecretStr = Field(min_length=8)

class UserRegisterDTO(BaseModel):
    email: EmailStr
    password1: SecretStr = Field(min_length=8)
    password2: SecretStr = Field(min_length=8)

    @model_validator(mode="after")
    def verify_passwords_match(self) -> Self:
        if self.password1.get_secret_value() != self.password2.get_secret_value():
            raise ValueError("Passwords don't match")
        return self

class UserInviteDTO(BaseModel):
    invitee_email: EmailStr
    grant_role: GrantProjectRole