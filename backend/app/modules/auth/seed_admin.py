from sqlalchemy import select

from app.core.config import settings
from app.core.data_mode import DataMode, normalize_data_mode
from app.core.security import hash_password
from app.db.session import get_session_factory
from app.modules.roles.models import Permission, Role
from app.modules.users.models import User

DEFAULT_PERMISSIONS = [
    ("users:manage", "Manage users"),
    ("roles:manage", "Manage roles and permissions"),
    ("sessions:manage", "Manage clinic sessions"),
    ("patients:read", "Read patient records"),
    ("patients:write", "Write patient records"),
    ("visits:manage", "Manage registration visits"),
    ("clinic:write", "Write clinic records"),
    ("prescriptions:confirm", "Confirm prescriptions"),
    ("pharmacy:dispense", "Dispense medication"),
    ("inventory:manage", "Manage inventory"),
    ("audit_logs:read", "Read audit logs"),
    ("exports:anonymous", "Export anonymized reports"),
    ("data_mode.live.access", "Access live data mode"),
    ("data_mode.demo.access", "Access demo data mode"),
    ("data_mode.switch", "Switch current data mode"),
    ("demo_data.manage", "Manage demo data"),
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
            else:
                permission.description = description
            permissions.append(permission)

        admin_role = db.execute(select(Role).where(Role.name == "admin")).scalar_one_or_none()
        if admin_role is None:
            admin_role = Role(name="admin", description="System administrator")
            db.add(admin_role)
        else:
            admin_role.description = "System administrator"
        admin_role.permissions = permissions

        admin = db.execute(select(User).where(User.username == settings.DEFAULT_ADMIN_USERNAME)).scalar_one_or_none()
        if admin is None:
            admin = User(
                username=settings.DEFAULT_ADMIN_USERNAME,
                email=settings.DEFAULT_ADMIN_EMAIL,
                full_name=settings.DEFAULT_ADMIN_FULL_NAME,
                password_hash=hash_password(settings.DEFAULT_ADMIN_PASSWORD),
                is_active=True,
                can_access_live=True,
                can_access_demo=True,
                default_data_mode=normalize_data_mode(settings.DEFAULT_DATA_MODE),
                current_data_mode=normalize_data_mode(settings.DEFAULT_DATA_MODE),
                roles=[admin_role],
            )
            db.add(admin)
        elif admin_role not in admin.roles:
            admin.roles.append(admin_role)

        if admin is not None:
            admin.can_access_live = True
            admin.can_access_demo = True
            admin.default_data_mode = normalize_data_mode(settings.DEFAULT_DATA_MODE, default=DataMode.LIVE)

        db.commit()


if __name__ == "__main__":
    seed_admin()
