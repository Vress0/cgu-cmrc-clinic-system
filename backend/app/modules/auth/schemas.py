from uuid import UUID

from pydantic import BaseModel, EmailStr, Field

from app.core.data_mode import DataMode


class LoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=80)
    password: str = Field(min_length=1, max_length=255)


class RefreshRequest(BaseModel):
    refresh_token: str = Field(min_length=20)


class LogoutRequest(BaseModel):
    refresh_token: str | None = Field(default=None, min_length=20)


class UserProfile(BaseModel):
    id: UUID
    username: str
    email: EmailStr
    full_name: str
    roles: list[str]
    permissions: list[str]
    data_mode: DataMode
    can_access_live: bool
    can_access_demo: bool


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserProfile
