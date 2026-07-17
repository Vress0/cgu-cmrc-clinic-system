from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from app.core.config import settings
from app.db.base import Base
from app.modules.auth import models as auth_models  # noqa: F401
from app.modules.audit_logs import models as audit_log_models  # noqa: F401
from app.modules.clinic_sessions import models as clinic_session_models  # noqa: F401
from app.modules.consultations import models as consultation_models  # noqa: F401
from app.modules.consents import models as consent_models  # noqa: F401
from app.modules.dispensing import models as dispensing_models  # noqa: F401
from app.modules.health_histories import models as health_history_models  # noqa: F401
from app.modules.inventory import models as inventory_models  # noqa: F401
from app.modules.medications import models as medication_models  # noqa: F401
from app.modules.patients import models as patient_models  # noqa: F401
from app.modules.prescriptions import models as prescription_models  # noqa: F401
from app.modules.queue import models as queue_models  # noqa: F401
from app.modules.roles import models as role_models  # noqa: F401
from app.modules.users import models as user_models  # noqa: F401
from app.modules.vital_signs import models as vital_sign_models  # noqa: F401
from app.modules.visits import models as visit_models  # noqa: F401

config = context.config
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    context.configure(
        url=settings.DATABASE_URL,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
