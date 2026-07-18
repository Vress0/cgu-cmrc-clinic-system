from datetime import datetime, timezone
from enum import Enum as PythonEnum
from uuid import UUID

from sqlalchemy import DateTime, Enum, ForeignKey, Numeric, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, DataModeScopedMixin, TimestampMixin, UUIDPrimaryKeyMixin


class BloodGlucoseContext(str, PythonEnum):
    FASTING = "fasting"
    BEFORE_MEAL = "before_meal"
    AFTER_MEAL = "after_meal"
    RANDOM = "random"
    UNKNOWN = "unknown"


class VitalSign(UUIDPrimaryKeyMixin, DataModeScopedMixin, TimestampMixin, Base):
    __tablename__ = "vital_signs"

    visit_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("visits.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    systolic_blood_pressure: Mapped[int | None] = mapped_column(nullable=True)
    diastolic_blood_pressure: Mapped[int | None] = mapped_column(nullable=True)
    pulse: Mapped[int | None] = mapped_column(nullable=True)
    temperature: Mapped[float | None] = mapped_column(Numeric(4, 1), nullable=True)
    oxygen_saturation: Mapped[int | None] = mapped_column(nullable=True)
    height_cm: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    weight_kg: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    bmi: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    blood_glucose: Mapped[float | None] = mapped_column(Numeric(6, 2), nullable=True)
    blood_glucose_context: Mapped[BloodGlucoseContext | None] = mapped_column(
        Enum(BloodGlucoseContext),
        nullable=True,
    )
    notes: Mapped[str] = mapped_column(Text, default="", nullable=False)
    measured_by: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        index=True,
        nullable=False,
    )
    measured_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        index=True,
        nullable=False,
    )

    visit = relationship("Visit", back_populates="vital_signs")
