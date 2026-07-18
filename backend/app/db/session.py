from functools import lru_cache

from sqlalchemy import event
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker, with_loader_criteria

from app.core.data_mode import DataMode, normalize_data_mode
from app.core.config import settings
from app.db.base import DataModeScopedMixin


def connect_args() -> dict[str, int]:
    if settings.DATABASE_URL.startswith("postgresql"):
        return {"connect_timeout": settings.DATABASE_CONNECT_TIMEOUT_SECONDS}
    return {}


@lru_cache
def get_engine() -> Engine:
    return create_engine(
        settings.DATABASE_URL,
        pool_pre_ping=True,
        connect_args=connect_args(),
    )


@lru_cache
def get_session_factory() -> sessionmaker[Session]:
    return sessionmaker(bind=get_engine(), autoflush=False, autocommit=False)


def get_db() -> Session:
    db = get_session_factory()()
    try:
        yield db
    finally:
        db.close()


@event.listens_for(Session, "do_orm_execute")
def apply_data_mode_scope(execute_state) -> None:
    if (
        not execute_state.is_select
        or execute_state.is_column_load
        or execute_state.is_relationship_load
        or execute_state.session.info.get("skip_data_mode_filter")
    ):
        return
    mode = execute_state.session.info.get("data_mode", DataMode.LIVE)
    execute_state.statement = execute_state.statement.options(
        with_loader_criteria(
            DataModeScopedMixin,
            lambda cls: cls.data_mode == mode,
            include_aliases=True,
        )
    )


@event.listens_for(Session, "before_flush")
def apply_data_mode_to_new_objects(session: Session, flush_context, instances) -> None:
    if session.info.get("skip_data_mode_filter"):
        return
    mode = normalize_data_mode(session.info.get("data_mode"), default=DataMode.LIVE)
    for obj in session.new:
        if isinstance(obj, DataModeScopedMixin) and getattr(obj, "data_mode", None) is None:
            obj.data_mode = mode


def check_database() -> bool:
    try:
        with get_engine().connect() as connection:
            connection.execute(text("SELECT 1"))
        return True
    except Exception:
        return False
