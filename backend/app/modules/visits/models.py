from datetime import datetime
from enum import Enum as PythonEnum
from uuid import UUID

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class VisitStatus(str, PythonEnum):
    REGISTERED = "REGISTERED"
    WAITING_FOR_CLINIC = "WAITING_FOR_CLINIC"
    IN_CONSULTATION = "IN_CONSULTATION"
    WAITING_FOR_PHARMACY = "WAITING_FOR_PHARMACY"
    DISPENSING = "DISPENSING"
    WAITING_FOR_VERIFICATION = "WAITING_FOR_VERIFICATION"
    WAITING_FOR_PICKUP = "WAITING_FOR_PICKUP"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class Visit(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "visits"
    __table_args__ = (
        UniqueConstraint("clinic_session_id", "patient_id", name="uq_visit_session_patient"),
    )

    clinic_session_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("clinic_sessions.id", ondelete="RESTRICT"),
        index=True,
        nullable=False,
    )
    patient_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("patients.id", ondelete="RESTRICT"),
        index=True,
        nullable=False,
    )
    queue_number: Mapped[int] = mapped_column(nullable=False)
    registered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[VisitStatus] = mapped_column(
        Enum(VisitStatus),
        default=VisitStatus.REGISTERED,
        index=True,
        nullable=False,
    )
    registration_staff: Mapped[str] = mapped_column(String(120), nullable=False)
    notes: Mapped[str] = mapped_column(Text, default="", nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    queue_record = relationship("QueueRecord", back_populates="visit", uselist=False)
    vital_signs = relationship("VitalSign", back_populates="visit")
    consultation = relationship("Consultation", back_populates="visit", uselist=False)
    prescription = relationship("Prescription", back_populates="visit", uselist=False)
