from datetime import datetime
from decimal import Decimal
from enum import Enum as PythonEnum
from uuid import UUID

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, Numeric, Text, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class PrescriptionStatus(str, PythonEnum):
    DRAFT = "DRAFT"
    CONFIRMED = "CONFIRMED"
    SENT_TO_PHARMACY = "SENT_TO_PHARMACY"
    DISPENSING = "DISPENSING"
    WAITING_FOR_VERIFICATION = "WAITING_FOR_VERIFICATION"
    VERIFIED = "VERIFIED"
    WAITING_FOR_PICKUP = "WAITING_FOR_PICKUP"
    DISPENSED = "DISPENSED"
    RETURNED_TO_CLINIC = "RETURNED_TO_CLINIC"
    VOIDED = "VOIDED"


class Prescription(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "prescriptions"
    __table_args__ = (UniqueConstraint("visit_id", name="uq_prescription_visit"),)

    visit_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("visits.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    status: Mapped[PrescriptionStatus] = mapped_column(
        Enum(PrescriptionStatus),
        default=PrescriptionStatus.DRAFT,
        index=True,
        nullable=False,
    )
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    created_by: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True), ForeignKey("users.id"), nullable=True)
    confirmed_by: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True), ForeignKey("users.id"), nullable=True)
    confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    sent_to_pharmacy_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    returned_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    returned_reason: Mapped[str] = mapped_column(Text, default="", nullable=False)
    voided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    void_reason: Mapped[str] = mapped_column(Text, default="", nullable=False)

    visit = relationship("Visit", back_populates="prescription")
    items = relationship(
        "PrescriptionItem",
        back_populates="prescription",
        cascade="all, delete-orphan",
        order_by="PrescriptionItem.created_at",
    )


class PrescriptionItem(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "prescription_items"

    prescription_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("prescriptions.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    medication_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("medications.id", ondelete="RESTRICT"),
        index=True,
        nullable=False,
    )
    dose: Mapped[str] = mapped_column(Text, nullable=False)
    dose_unit: Mapped[str] = mapped_column(Text, nullable=False)
    frequency: Mapped[str] = mapped_column(Text, nullable=False)
    route: Mapped[str] = mapped_column(Text, default="", nullable=False)
    duration_days: Mapped[int | None] = mapped_column(Integer, nullable=True)
    quantity: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    instructions: Mapped[str] = mapped_column(Text, default="", nullable=False)
    notes: Mapped[str] = mapped_column(Text, default="", nullable=False)

    medication = relationship("Medication", back_populates="prescription_items")
    prescription = relationship("Prescription", back_populates="items")
