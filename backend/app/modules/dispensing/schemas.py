from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field

from app.modules.dispensing.models import DispensingStatus, ReturnReason
from app.modules.inventory.schemas import InventoryBatchRead
from app.modules.medications.schemas import MedicationRead
from app.modules.prescriptions.schemas import PrescriptionItemRead, PrescriptionRead
from app.modules.visits.models import VisitStatus


class DispensingItemUpdate(BaseModel):
    id: UUID
    dispensed_quantity: Decimal = Field(gt=0, decimal_places=2, max_digits=10)
    notes: str = ""


class DispensingItemsUpdate(BaseModel):
    items: list[DispensingItemUpdate] = Field(min_length=1)
    notes: str = ""


class DispensingVerify(BaseModel):
    allow_self_verification: bool = False
    exception_reason: str = Field(default="", max_length=1000)


class DispensingHandOut(BaseModel):
    patient_counseling: str = Field(min_length=1, max_length=5000)
    notes: str = ""
    idempotency_key: str = Field(min_length=8, max_length=120)


class DispensingReturn(BaseModel):
    reason: ReturnReason
    details: str = Field(min_length=1, max_length=5000)


class DispensingItemRead(BaseModel):
    id: UUID
    dispensing_record_id: UUID
    prescription_item_id: UUID
    medication_id: UUID
    prescribed_quantity: Decimal
    dispensed_quantity: Decimal
    unit: str
    notes: str
    inventory_batch_id: UUID | None
    inventory_batch: InventoryBatchRead | None = None
    medication: MedicationRead
    prescription_item: PrescriptionItemRead
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class DispensingRecordRead(BaseModel):
    id: UUID
    visit_id: UUID
    prescription_id: UUID
    status: DispensingStatus
    assigned_to: UUID | None
    started_at: datetime | None
    prepared_by: UUID | None
    prepared_at: datetime | None
    verified_by: UUID | None
    verified_at: datetime | None
    verification_exception: bool
    verification_exception_reason: str
    handed_out_by: UUID | None
    handed_out_at: datetime | None
    patient_counseling: str
    notes: str
    return_reason: ReturnReason | None
    return_details: str
    returned_by: UUID | None
    returned_at: datetime | None
    version: int
    created_by: UUID | None
    updated_by: UUID | None
    items: list[DispensingItemRead]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PharmacyQueueItem(BaseModel):
    visit_id: UUID
    clinic_session_id: UUID
    clinic_session_name: str
    session_date: date
    patient_id: UUID
    patient_case_number: str
    patient_name: str
    patient_sex: str
    queue_number: int
    visit_status: VisitStatus
    prescription_id: UUID
    prescription_status: str
    dispensing_id: UUID | None = None
    dispensing_status: DispensingStatus | None = None
    item_count: int
    total_quantity: Decimal
    assigned_to: UUID | None = None
    started_at: datetime | None = None
    prepared_at: datetime | None = None
    verified_at: datetime | None = None
    handed_out_at: datetime | None = None
    notes: str


class PharmacyVisitDetail(BaseModel):
    queue_item: PharmacyQueueItem
    prescription: PrescriptionRead
    dispensing: DispensingRecordRead | None = None
