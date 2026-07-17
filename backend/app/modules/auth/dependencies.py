from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import InvalidTokenError
from sqlalchemy.orm import Session

from app.core.security import decode_token
from app.db.session import get_db
from app.modules.auth.repository import get_user_by_id
from app.modules.auth.service import user_permissions
from app.modules.users.models import User

bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="尚未登入")
    try:
        payload = decode_token(credentials.credentials)
        if payload.get("typ") != "access":
            raise InvalidTokenError
        user_id = UUID(str(payload["sub"]))
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token 無效") from exc

    user = get_user_by_id(db, user_id)
    if user is None or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="帳號無效")
    return user


def require_permissions(*required_permissions: str):
    def dependency(current_user: User = Depends(get_current_user)) -> User:
        granted = set(user_permissions(current_user))
        missing = [permission for permission in required_permissions if permission not in granted]
        if missing:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="權限不足")
        return current_user

    return dependency
