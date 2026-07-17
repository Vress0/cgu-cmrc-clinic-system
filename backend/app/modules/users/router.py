from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.db.session import get_db
from app.modules.audit_logs.service import write_audit_log
from app.modules.auth.dependencies import require_permissions
from app.modules.auth.service import user_role_names
from app.modules.roles.models import Permission, Role
from app.modules.users.models import User
from app.modules.users.schemas import (
    ManagedUserCreate,
    ManagedUserRead,
    ManagedUserUpdate,
    PasswordReset,
    RoleRead,
)

router = APIRouter(tags=["users"])

ROLE_PERMISSIONS: dict[str, list[str]] = {
    "admin": [
        "users:manage",
        "roles:manage",
        "sessions:manage",
        "patients:read",
        "patients:write",
        "visits:manage",
        "clinic:write",
        "prescriptions:confirm",
        "pharmacy:dispense",
        "inventory:manage",
        "audit_logs:read",
        "exports:anonymous",
    ],
    "registration": ["sessions:manage", "patients:read", "patients:write", "visits:manage"],
    "clinic_student": ["patients:read", "clinic:write"],
    "clinician": ["patients:read", "clinic:write", "prescriptions:confirm"],
    "pharmacy": ["patients:read", "pharmacy:dispense"],
}


def ensure_default_roles(db: Session) -> None:
    for role_name, permission_codes in ROLE_PERMISSIONS.items():
        role = db.execute(select(Role).where(Role.name == role_name)).scalar_one_or_none()
        if role is None:
            role = Role(name=role_name, description=role_name)
            db.add(role)
        permissions = list(db.execute(select(Permission).where(Permission.code.in_(permission_codes))).scalars())
        role.permissions = permissions
    db.flush()


def serialize_user(user: User) -> ManagedUserRead:
    return ManagedUserRead(
        id=user.id,
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        is_active=user.is_active,
        failed_login_count=user.failed_login_count,
        locked_until=user.locked_until,
        last_login_at=user.last_login_at,
        roles=user_role_names(user),
        created_at=user.created_at,
        updated_at=user.updated_at,
    )


def roles_by_name(db: Session, names: list[str]) -> list[Role]:
    ensure_default_roles(db)
    if not names:
        return []
    roles = list(db.execute(select(Role).where(Role.name.in_(names))).scalars())
    found = {role.name for role in roles}
    missing = sorted(set(names) - found)
    if missing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Roles not found: {', '.join(missing)}")
    return roles


@router.get("/roles", response_model=list[RoleRead])
def list_roles(
    db: Session = Depends(get_db),
    _=Depends(require_permissions("users:manage")),
) -> list[RoleRead]:
    ensure_default_roles(db)
    db.commit()
    roles = list(db.execute(select(Role).order_by(Role.name.asc())).scalars())
    return [
        RoleRead(
            id=role.id,
            name=role.name,
            description=role.description,
            permissions=sorted(permission.code for permission in role.permissions),
        )
        for role in roles
    ]


@router.get("/users", response_model=list[ManagedUserRead])
def list_users(
    db: Session = Depends(get_db),
    _=Depends(require_permissions("users:manage")),
) -> list[ManagedUserRead]:
    users = list(db.execute(select(User).order_by(User.created_at.desc())).scalars())
    return [serialize_user(user) for user in users]


@router.post("/users", response_model=ManagedUserRead, status_code=201)
def create_user(
    payload: ManagedUserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions("users:manage")),
) -> ManagedUserRead:
    user = User(
        username=payload.username,
        email=payload.email,
        full_name=payload.full_name,
        password_hash=hash_password(payload.password),
        is_active=payload.is_active,
        roles=roles_by_name(db, payload.roles),
    )
    db.add(user)
    try:
        db.flush()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Username or email already exists") from exc
    write_audit_log(
        db,
        actor_user_id=current_user.id,
        action="USER_CREATED",
        entity_type="user",
        entity_id=user.id,
        summary=f"Created user {user.username}",
    )
    db.commit()
    db.refresh(user)
    return serialize_user(user)


@router.patch("/users/{user_id}", response_model=ManagedUserRead)
def update_user(
    user_id: UUID,
    payload: ManagedUserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions("users:manage")),
) -> ManagedUserRead:
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    values = payload.model_dump(exclude_unset=True)
    if "email" in values:
        user.email = values["email"]
    if "full_name" in values:
        user.full_name = values["full_name"]
    if "is_active" in values:
        user.is_active = values["is_active"]
    if payload.roles is not None:
        user.roles = roles_by_name(db, payload.roles)
    if payload.unlock:
        user.failed_login_count = 0
        user.locked_until = None
    try:
        db.flush()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already exists") from exc
    write_audit_log(
        db,
        actor_user_id=current_user.id,
        action="USER_UPDATED",
        entity_type="user",
        entity_id=user.id,
        summary=f"Updated user {user.username}",
    )
    db.commit()
    db.refresh(user)
    return serialize_user(user)


@router.post("/users/{user_id}/reset-password", response_model=ManagedUserRead)
def reset_password(
    user_id: UUID,
    payload: PasswordReset,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions("users:manage")),
) -> ManagedUserRead:
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    user.password_hash = hash_password(payload.password)
    user.failed_login_count = 0
    user.locked_until = None
    write_audit_log(
        db,
        actor_user_id=current_user.id,
        action="USER_PASSWORD_RESET",
        entity_type="user",
        entity_id=user.id,
        summary=f"Reset password for user {user.username}",
    )
    db.commit()
    db.refresh(user)
    return serialize_user(user)
