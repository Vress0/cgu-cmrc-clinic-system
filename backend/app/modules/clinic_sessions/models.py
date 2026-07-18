from datetime import date, time
from enum import Enum as PythonEnum

from sqlalchemy import Date, Enum, String, Text, Time, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, DataModeScopedMixin, TimestampMixin, UUIDPrimaryKeyMixin


class ClinicSessionStatus(str, PythonEnum):
    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    ENDED = "ENDED"
    ARCHIVED = "ARCHIVED"


class ClinicSession(UUIDPrimaryKeyMixin, DataModeScopedMixin, TimestampMixin, Base):
    __tablename__ = "clinic_sessions"
    __table_args__ = (UniqueConstraint("data_mode", "name", "session_date", name="uq_session_mode_name_date"),)

    name: Mapped[str] = mapped_column(String(120), nullable=False)
    session_date: Mapped[date] = mapped_column(Date, index=True, nullable=False)
    start_time: Mapped[time | None] = mapped_column(Time, nullable=True)
    end_time: Mapped[time | None] = mapped_column(Time, nullable=True)
    location: Mapped[str] = mapped_column(String(160), nullable=False)
    owner: Mapped[str] = mapped_column(String(120), nullable=False)
    notes: Mapped[str] = mapped_column(Text, default="", nullable=False)
    status: Mapped[ClinicSessionStatus] = mapped_column(
        Enum(ClinicSessionStatus),
        default=ClinicSessionStatus.DRAFT,
        index=True,
        nullable=False,
    )
