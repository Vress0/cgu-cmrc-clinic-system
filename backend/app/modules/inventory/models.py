from datetime import date, datetime
from decimal import Decimal
from enum import Enum as PythonEnum
from uuid import UUID

from sqlalchemy import Boolean, CheckConstraint, Date, DateTime, Enum, ForeignKey, Integer, Numeric, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class InventoryTransactionType(str, PythonEnum):
    RECEIVE = "RECEIVE"
    RESERVE = "RESERVE"
    RELEASE = "RELEASE"
    DISPENSE = "DISPENSE"
    RETURN = "RETURN"
    ADJUST_INCREASE = "ADJUST_INCREASE"
    ADJUST_DECREASE = "ADJUST_DECREASE"
    EXPIRE = "EXPIRE"
    DISCARD = "DISCARD"


class InventoryBatch(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "inventory_batches"
    __table_args__ = (
        CheckConstraint("quantity_on_hand >= 0", name="ck_inventory_batches_quantity_nonnegative"),
        CheckConstraint("reserved_quantity >= 0", name="ck_inventory_batches_reserved_nonnegative"),
        CheckConstraint(
            "reserved_quantity <= quantity_on_hand",
            name="ck_inventory_batches_reserved_lte_on_hand",
        ),
    )

    medication_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("medications.id", ondelete="RESTRICT"), index=True, nullable=False
    )
    batch_number: Mapped[str] = mapped_column(String(120), index=True, nullable=False)
    expiry_date: Mapped[date] = mapped_column(Date, index=True, nullable=False)
    quantity_on_hand: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    reserved_quantity: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("0.00"), nullable=False)
    unit: Mapped[str] = mapped_column(String(40), nullable=False)
    location: Mapped[str] = mapped_column(String(160), default="", nullable=False)
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True, nullable=False)
    created_by: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True), ForeignKey("users.id"), nullable=True)
    updated_by: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True), ForeignKey("users.id"), nullable=True)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    medication = relationship("Medication")
    transactions = relationship("InventoryTransaction", back_populates="inventory_batch")

    @property
    def available_quantity(self) -> Decimal:
        return self.quantity_on_hand - self.reserved_quantity


class InventoryTransaction(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "inventory_transactions"

    medication_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("medications.id", ondelete="RESTRICT"), index=True, nullable=False
    )
    inventory_batch_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("inventory_batches.id", ondelete="RESTRICT"), index=True, nullable=False
    )
    transaction_type: Mapped[InventoryTransactionType] = mapped_column(
        Enum(InventoryTransactionType), index=True, nullable=False
    )
    quantity: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    quantity_before: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    quantity_after: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    reserved_before: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    reserved_after: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    reference_type: Mapped[str] = mapped_column(String(80), default="", nullable=False)
    reference_id: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True), nullable=True)
    reason: Mapped[str] = mapped_column(Text, default="", nullable=False)
    performed_by: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True), ForeignKey("users.id"), nullable=True)
    idempotency_key: Mapped[str | None] = mapped_column(String(120), unique=True, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    inventory_batch = relationship("InventoryBatch", back_populates="transactions")
    medication = relationship("Medication")
