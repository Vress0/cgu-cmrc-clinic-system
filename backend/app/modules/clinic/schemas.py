from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel

from app.modules.visits.models import VisitStatus


class ClinicQueueItem(BaseModel):
    visit_id: UUID
    clinic_session_id: UUID
    clinic_session_name: str
    session_date: date
    patient_id: UUID
    patient_case_number: str
    patient_name: str
    patient_sex: str
    queue_number: int
    status: VisitStatus
    registered_at: datetime
    notes: str
    latest_vital_sign_at: datetime | None = None
    has_consultation: bool = False
