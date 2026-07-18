from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.core.data_mode import DataMode


class ManagedUserRead(BaseModel):
    id: UUID
    username: str
    email: str
    full_name: str
    is_active: bool
    failed_login_count: int
    locked_until: datetime | None
    last_login_at: datetime | None
    roles: list[str]
    can_access_live: bool
    can_access_demo: bool
    default_data_mode: DataMode
    current_data_mode: DataMode
    created_at: datetime
    updated_at: datetime


class ManagedUserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=80)
    email: str = Field(min_length=3, max_length=255)
    full_name: str = Field(min_length=1, max_length=120)
    password: str = Field(min_length=8, max_length=128)
    roles: list[str] = Field(default_factory=list)
    is_active: bool = True
    can_access_live: bool = True
    can_access_demo: bool = True
    default_data_mode: DataMode = DataMode.LIVE


class ManagedUserUpdate(BaseModel):
    email: str | None = Field(default=None, min_length=3, max_length=255)
    full_name: str | None = Field(default=None, min_length=1, max_length=120)
    roles: list[str] | None = None
    is_active: bool | None = None
    can_access_live: bool | None = None
    can_access_demo: bool | None = None
    default_data_mode: DataMode | None = None
    current_data_mode: DataMode | None = None
    unlock: bool = False


class PasswordReset(BaseModel):
    password: str = Field(min_length=8, max_length=128)


class RoleRead(BaseModel):
    id: UUID
    name: str
    description: str
    permissions: list[str]
