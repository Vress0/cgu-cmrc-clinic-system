from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field

from app.modules.medications.schemas import MedicationRead
from app.modules.prescriptions.models import PrescriptionStatus


class PrescriptionItemBase(BaseModel):
    medication_id: UUID
    dose: str = Field(min_length=1, max_length=120)
    dose_unit: str = Field(min_length=1, max_length=80)
    frequency: str = Field(min_length=1, max_length=120)
    route: str = Field(default="", max_length=80)
    duration_days: int | None = Field(default=None, ge=1, le=365)
    quantity: Decimal = Field(gt=0, decimal_places=2, max_digits=10)
    instructions: str = ""
    notes: str = ""


class PrescriptionItemCreate(PrescriptionItemBase):
    pass


class PrescriptionItemUpdate(BaseModel):
    medication_id: UUID | None = None
    dose: str | None = Field(default=None, min_length=1, max_length=120)
    dose_unit: str | None = Field(default=None, min_length=1, max_length=80)
    frequency: str | None = Field(default=None, min_length=1, max_length=120)
    route: str | None = Field(default=None, max_length=80)
    duration_days: int | None = Field(default=None, ge=1, le=365)
    quantity: Decimal | None = Field(default=None, gt=0, decimal_places=2, max_digits=10)
    instructions: str | None = None
    notes: str | None = None


class PrescriptionItemRead(PrescriptionItemBase):
    id: UUID
    prescription_id: UUID
    medication: MedicationRead
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PrescriptionCreate(BaseModel):
    pass


class PrescriptionRead(BaseModel):
    id: UUID
    visit_id: UUID
    status: PrescriptionStatus
    version: int
    created_by: UUID | None
    confirmed_by: UUID | None
    confirmed_at: datetime | None
    sent_to_pharmacy_at: datetime | None
    returned_at: datetime | None
    returned_reason: str
    voided_at: datetime | None
    void_reason: str
    items: list[PrescriptionItemRead]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PrescriptionVoid(BaseModel):
    reason: str = Field(default="", max_length=1000)
