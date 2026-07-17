from datetime import datetime
from decimal import Decimal
from enum import Enum as PythonEnum
from uuid import UUID

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, Numeric, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class DispensingStatus(str, PythonEnum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    WAITING_FOR_VERIFICATION = "WAITING_FOR_VERIFICATION"
    VERIFIED = "VERIFIED"
    WAITING_FOR_PICKUP = "WAITING_FOR_PICKUP"
    DISPENSED = "DISPENSED"
    RETURNED = "RETURNED"
    CANCELLED = "CANCELLED"


class ReturnReason(str, PythonEnum):
    OUT_OF_STOCK = "OUT_OF_STOCK"
    UNCLEAR_DOSAGE = "UNCLEAR_DOSAGE"
    UNCLEAR_INSTRUCTIONS = "UNCLEAR_INSTRUCTIONS"
    INCORRECT_QUANTITY = "INCORRECT_QUANTITY"
    ALLERGY_RISK = "ALLERGY_RISK"
    DUPLICATE_MEDICATION = "DUPLICATE_MEDICATION"
    OTHER = "OTHER"


class DispensingRecord(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "dispensing_records"

    visit_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("visits.id", ondelete="CASCADE"), index=True)
    prescription_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("prescriptions.id", ondelete="CASCADE"), index=True
    )
    status: Mapped[DispensingStatus] = mapped_column(
        Enum(DispensingStatus), default=DispensingStatus.PENDING, index=True, nullable=False
    )
    assigned_to: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True), ForeignKey("users.id"), nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    prepared_by: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True), ForeignKey("users.id"), nullable=True)
    prepared_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    verified_by: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True), ForeignKey("users.id"), nullable=True)
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    verification_exception: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    verification_exception_reason: Mapped[str] = mapped_column(Text, default="", nullable=False)
    handed_out_by: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True), ForeignKey("users.id"), nullable=True)
    handed_out_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    patient_counseling: Mapped[str] = mapped_column(Text, default="", nullable=False)
    notes: Mapped[str] = mapped_column(Text, default="", nullable=False)
    return_reason: Mapped[ReturnReason | None] = mapped_column(Enum(ReturnReason), nullable=True)
    return_details: Mapped[str] = mapped_column(Text, default="", nullable=False)
    returned_by: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True), ForeignKey("users.id"), nullable=True)
    returned_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    handout_idempotency_key: Mapped[str | None] = mapped_column(String(120), unique=True, nullable=True)
    created_by: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True), ForeignKey("users.id"), nullable=True)
    updated_by: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True), ForeignKey("users.id"), nullable=True)

    items = relationship(
        "DispensingItem",
        back_populates="dispensing_record",
        cascade="all, delete-orphan",
        order_by="DispensingItem.created_at",
    )
    prescription = relationship("Prescription")
    visit = relationship("Visit")


class DispensingItem(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "dispensing_items"

    dispensing_record_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("dispensing_records.id", ondelete="CASCADE"), index=True
    )
    prescription_item_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("prescription_items.id", ondelete="RESTRICT"), index=True
    )
    medication_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("medications.id", ondelete="RESTRICT"), index=True)
    prescribed_quantity: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    dispensed_quantity: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    unit: Mapped[str] = mapped_column(String(40), default="", nullable=False)
    notes: Mapped[str] = mapped_column(Text, default="", nullable=False)
    inventory_batch_id: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True), nullable=True)

    dispensing_record = relationship("DispensingRecord", back_populates="items")
    medication = relationship("Medication")
    prescription_item = relationship("PrescriptionItem")
