from pydantic import BaseModel, EmailStr, ConfigDict
from datetime import datetime

class UserBase(BaseModel):
    email: EmailStr
    username: str

class UserCreate(UserBase):
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

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
    full_name: str | None = None
    bio: str | None = None
    avatar_url: str | None = None
    language: str | None = None

class PasswordChange(BaseModel):
    old_password: str
    new_password: str

class PasswordResetRequest(BaseModel):
    email: EmailStr

class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str

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
