from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field

from app.modules.inventory.models import InventoryTransactionType
from app.modules.medications.schemas import MedicationRead


class InventoryBatchCreate(BaseModel):
    medication_id: UUID
    batch_number: str = Field(min_length=1, max_length=120)
    expiry_date: date
    quantity: Decimal = Field(gt=0, decimal_places=2, max_digits=10)
    unit: str = Field(min_length=1, max_length=40)
    location: str = Field(default="", max_length=160)
    received_at: datetime | None = None


class InventoryBatchUpdate(BaseModel):
    batch_number: str | None = Field(default=None, min_length=1, max_length=120)
    expiry_date: date | None = None
    unit: str | None = Field(default=None, min_length=1, max_length=40)
    location: str | None = Field(default=None, max_length=160)
    is_active: bool | None = None


class InventoryAdjustmentCreate(BaseModel):
    batch_id: UUID
    adjustment_type: InventoryTransactionType
    quantity: Decimal = Field(gt=0, decimal_places=2, max_digits=10)
    reason: str = Field(min_length=1, max_length=5000)


class InventoryBatchRead(BaseModel):
    id: UUID
    medication_id: UUID
    medication: MedicationRead
    batch_number: str
    expiry_date: date
    quantity_on_hand: Decimal
    reserved_quantity: Decimal
    available_quantity: Decimal
    unit: str
    location: str
    received_at: datetime
    is_active: bool
    created_by: UUID | None
    updated_by: UUID | None
    version: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class InventoryTransactionRead(BaseModel):
    id: UUID
    medication_id: UUID
    inventory_batch_id: UUID
    transaction_type: InventoryTransactionType
    quantity: Decimal
    quantity_before: Decimal
    quantity_after: Decimal
    reserved_before: Decimal
    reserved_after: Decimal
    reference_type: str
    reference_id: UUID | None
    reason: str
    performed_by: UUID | None
    idempotency_key: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class InventorySummary(BaseModel):
    batch_count: int
    active_batch_count: int
    total_on_hand: Decimal
    total_reserved: Decimal
    total_available: Decimal
    low_stock_count: int
    expiring_count: int
    expired_count: int
