from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.modules.visits.models import VisitStatus


class VisitCreate(BaseModel):
    clinic_session_id: UUID
    patient_id: UUID
    registration_staff: str = Field(min_length=1, max_length=120)
    notes: str = ""


class VisitStatusUpdate(BaseModel):
    status: VisitStatus


class VisitRead(BaseModel):
    id: UUID
    clinic_session_id: UUID
    patient_id: UUID
    queue_number: int
    registered_at: datetime
    status: VisitStatus
    registration_staff: str
    notes: str
    completed_at: datetime | None

    model_config = {"from_attributes": True}
