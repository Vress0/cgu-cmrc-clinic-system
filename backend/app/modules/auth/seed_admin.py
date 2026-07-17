from sqlalchemy import select

from app.core.config import settings
from app.core.security import hash_password
from app.db.session import get_session_factory
from app.modules.roles.models import Permission, Role
from app.modules.users.models import User

DEFAULT_PERMISSIONS = [
    ("users:manage", "管理帳號"),
    ("roles:manage", "管理角色與權限"),
    ("sessions:manage", "管理義診場次"),
    ("patients:read", "查看個案資料"),
    ("patients:write", "新增或修改個案資料"),
    ("visits:manage", "管理掛號與流程狀態"),
    ("clinic:write", "填寫診間資料"),
    ("prescriptions:confirm", "確認用藥單"),
    ("pharmacy:dispense", "調劑、核對與發藥"),
    ("inventory:manage", "管理藥品庫存"),
    ("audit_logs:read", "查看稽核紀錄"),
    ("exports:anonymous", "匯出匿名統計資料"),
]


def seed_admin() -> None:
    session_factory = get_session_factory()
    with session_factory() as db:
        permissions: list[Permission] = []
        for code, description in DEFAULT_PERMISSIONS:
            permission = db.execute(select(Permission).where(Permission.code == code)).scalar_one_or_none()
            if permission is None:
                permission = Permission(code=code, description=description)
                db.add(permission)
            permissions.append(permission)

        admin_role = db.execute(select(Role).where(Role.name == "admin")).scalar_one_or_none()
        if admin_role is None:
            admin_role = Role(name="admin", description="系統管理員")
            db.add(admin_role)
        admin_role.permissions = permissions

        admin = db.execute(
            select(User).where(User.username == settings.DEFAULT_ADMIN_USERNAME)
        ).scalar_one_or_none()
        if admin is None:
            admin = User(
                username=settings.DEFAULT_ADMIN_USERNAME,
                email=settings.DEFAULT_ADMIN_EMAIL,
                full_name="系統管理員",
                password_hash=hash_password(settings.DEFAULT_ADMIN_PASSWORD),
                is_active=True,
                roles=[admin_role],
            )
            db.add(admin)
        elif admin_role not in admin.roles:
            admin.roles.append(admin_role)

        db.commit()


if __name__ == "__main__":
    seed_admin()
