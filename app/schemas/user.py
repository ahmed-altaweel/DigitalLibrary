from pydantic import BaseModel, EmailStr, ConfigDict, Field, field_validator
from datetime import datetime
import re

USERNAME_RE = re.compile(r"^[\w.-]+$", re.UNICODE)


def _check_password_strength(value: str) -> str:
    if not any(c.isalpha() for c in value) or not any(c.isdigit() for c in value):
        raise ValueError("Password must contain at least one letter and one digit")
    return value

class UserBase(BaseModel):
    email: EmailStr
    username: str = Field(min_length=3, max_length=50)

    @field_validator("username")
    @classmethod
    def _valid_username(cls, v: str) -> str:
        if not USERNAME_RE.match(v):
            raise ValueError("Username may only contain letters, digits, '_', '.' and '-'")
        return v

class UserCreate(UserBase):
    password: str = Field(min_length=8, max_length=128)

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        return _check_password_strength(v)

class UserLogin(BaseModel):
    email: EmailStr
    password: str = Field(max_length=128)

class UserResponse(UserBase):
    id: str
    full_name: str | None = None
    bio: str | None = None
    avatar_url: str | None = None
    is_active: bool
    is_verified: bool
    language: str
    created_at: datetime
    updated_at: datetime | None = None
    model_config = ConfigDict(from_attributes=True)

class UserUpdate(BaseModel):
    full_name: str | None = Field(default=None, max_length=255)
    bio: str | None = Field(default=None, max_length=2000)
    avatar_url: str | None = Field(default=None, max_length=500)
    language: str | None = Field(default=None, max_length=10)

class PasswordChange(BaseModel):
    old_password: str = Field(max_length=128)
    new_password: str = Field(min_length=8, max_length=128)

    @field_validator("new_password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        return _check_password_strength(v)

class PasswordResetRequest(BaseModel):
    email: EmailStr

class PasswordResetConfirm(BaseModel):
    token: str = Field(max_length=256)
    new_password: str = Field(min_length=8, max_length=128)

    @field_validator("new_password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        return _check_password_strength(v)

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class RoleResponse(BaseModel):
    id: str
    name: str
    model_config = ConfigDict(from_attributes=True)

class UserWithRoles(UserResponse):
    roles: list[RoleResponse] = []
