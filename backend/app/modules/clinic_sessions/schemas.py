from datetime import date, time
from uuid import UUID

from pydantic import BaseModel, Field

from app.modules.clinic_sessions.models import ClinicSessionStatus


class ClinicSessionCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    session_date: date
    start_time: time | None = None
    end_time: time | None = None
    location: str = Field(min_length=1, max_length=160)
    owner: str = Field(min_length=1, max_length=120)
    notes: str = ""
    status: ClinicSessionStatus = ClinicSessionStatus.DRAFT


class ClinicSessionRead(ClinicSessionCreate):
    id: UUID

    model_config = {"from_attributes": True}
