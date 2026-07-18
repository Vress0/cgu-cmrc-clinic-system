from datetime import datetime, timedelta, timezone
from hashlib import sha256
from secrets import token_urlsafe
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.data_mode import normalize_data_mode
from app.core.security import create_access_token, verify_password
from app.modules.auth.models import RefreshToken
from app.modules.auth.repository import (
    get_refresh_token_by_hash,
    get_user_by_id,
    get_user_by_username,
    revoke_refresh_token,
)
from app.modules.auth.schemas import TokenResponse, UserProfile
from app.modules.users.models import User


def token_hash(token: str) -> str:
    return sha256(token.encode("utf-8")).hexdigest()


def user_permissions(user: User) -> list[str]:
    permissions = {permission.code for role in user.roles for permission in role.permissions}
    return sorted(permissions)


def user_role_names(user: User) -> list[str]:
    return sorted(role.name for role in user.roles)


def user_profile(user: User) -> UserProfile:
    data_mode = normalize_data_mode(user.current_data_mode, default=normalize_data_mode(settings.DEFAULT_DATA_MODE))
    return UserProfile(
        id=user.id,
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        roles=user_role_names(user),
        permissions=user_permissions(user),
        data_mode=data_mode,
        can_access_live=user.can_access_live,
        can_access_demo=settings.ENABLE_DEMO_MODE and user.can_access_demo,
    )


def create_refresh_token(db: Session, user_id: UUID) -> str:
    raw_token = token_urlsafe(48)
    db.add(
        RefreshToken(
            user_id=user_id,
            token_hash=token_hash(raw_token),
            expires_at=datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
        )
    )
    return raw_token


def is_expired(expires_at: datetime, now: datetime) -> bool:
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    return expires_at <= now


def build_token_response(db: Session, user: User) -> TokenResponse:
    roles = user_role_names(user)
    permissions = user_permissions(user)
    access_token = create_access_token(user.id, roles, permissions)
    refresh_token = create_refresh_token(db, user.id)
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=user_profile(user),
    )


def authenticate_user(db: Session, username: str, password: str) -> TokenResponse:
    user = get_user_by_username(db, username)
    invalid_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="帳號或密碼錯誤",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if user is None or not user.is_active:
        raise invalid_error

    now = datetime.now(timezone.utc)
    if user.locked_until and user.locked_until > now:
        raise HTTPException(status_code=status.HTTP_423_LOCKED, detail="帳號暫時鎖定，請稍後再試")

    if not verify_password(password, user.password_hash):
        user.failed_login_count += 1
        if user.failed_login_count >= 5:
            user.locked_until = now + timedelta(minutes=15)
        db.add(user)
        db.commit()
        raise invalid_error

    user.failed_login_count = 0
    user.locked_until = None
    user.last_login_at = now
    db.add(user)
    response = build_token_response(db, user)
    db.commit()
    return response


def refresh_access_token(db: Session, refresh_token: str) -> TokenResponse:
    stored_token = get_refresh_token_by_hash(db, token_hash(refresh_token))
    now = datetime.now(timezone.utc)
    if stored_token is None or stored_token.revoked_at is not None or is_expired(stored_token.expires_at, now):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token 無效")

    user = get_user_by_id(db, stored_token.user_id)
    if user is None or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="帳號無效")

    revoke_refresh_token(db, stored_token)
    response = build_token_response(db, user)
    db.commit()
    return response


def logout(db: Session, refresh_token: str | None) -> None:
    if not refresh_token:
        return
    stored_token = get_refresh_token_by_hash(db, token_hash(refresh_token))
    if stored_token and stored_token.revoked_at is None:
        revoke_refresh_token(db, stored_token)
        db.commit()
