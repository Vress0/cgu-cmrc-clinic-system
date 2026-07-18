from uuid import UUID

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import InvalidTokenError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.data_mode import DataMode, normalize_data_mode
from app.core.security import decode_token
from app.db.session import get_db
from app.modules.auth.repository import get_user_by_id
from app.modules.auth.service import user_permissions
from app.modules.users.models import User

bearer_scheme = HTTPBearer(auto_error=False)


def resolve_user_data_mode(user: User) -> DataMode:
    default = normalize_data_mode(settings.DEFAULT_DATA_MODE)
    requested = normalize_data_mode(user.current_data_mode, default=default)
    if not settings.ENABLE_DEMO_MODE and requested == DataMode.DEMO:
        requested = DataMode.LIVE

    if requested == DataMode.DEMO:
        if user.can_access_demo and settings.ENABLE_DEMO_MODE:
            return DataMode.DEMO
        if user.can_access_live:
            return DataMode.LIVE
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No demo data access")

    if user.can_access_live:
        return DataMode.LIVE
    if settings.ENABLE_DEMO_MODE and user.can_access_demo:
        return DataMode.DEMO
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No data mode access")


def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    try:
        payload = decode_token(credentials.credentials)
        if payload.get("typ") != "access":
            raise InvalidTokenError
        user_id = UUID(str(payload["sub"]))
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token") from exc

    user = get_user_by_id(db, user_id)
    if user is None or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid user")

    data_mode = resolve_user_data_mode(user)
    db.info["data_mode"] = data_mode
    db.info["data_mode_actor_id"] = user.id
    request.state.data_mode = data_mode
    return user


def require_permissions(*required_permissions: str):
    def dependency(current_user: User = Depends(get_current_user)) -> User:
        granted = set(user_permissions(current_user))
        missing = [permission for permission in required_permissions if permission not in granted]
        if missing:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied")
        return current_user

    return dependency
