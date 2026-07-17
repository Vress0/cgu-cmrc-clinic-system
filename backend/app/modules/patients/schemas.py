from datetime import date
from uuid import UUID

from pydantic import BaseModel, Field


class PatientCreate(BaseModel):
    case_number: str = Field(min_length=1, max_length=40)
    name: str = Field(min_length=1, max_length=80)
    sex: str = Field(min_length=1, max_length=20)
    birth_date: date | None = None
    phone: str = ""
    residence_area: str = ""
    emergency_contact: str = ""
    emergency_contact_phone: str = ""
    primary_language: str = ""
    assistance_needs: str = ""


class PatientUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=80)
    sex: str | None = Field(default=None, min_length=1, max_length=20)
    birth_date: date | None = None
    phone: str | None = None
    residence_area: str | None = None
    emergency_contact: str | None = None
    emergency_contact_phone: str | None = None
    primary_language: str | None = None
    assistance_needs: str | None = None
    is_active: bool | None = None


class PatientRead(PatientCreate):
    id: UUID
    is_active: bool

    model_config = {"from_attributes": True}
