from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, model_validator


class ConsentCreate(BaseModel):
    version: str = Field(min_length=1, max_length=40)
    method: str = Field(min_length=1, max_length=40)
    consented_at: datetime
    staff_name: str = Field(min_length=1, max_length=120)
    service_consent: bool
    research_consent: bool = False
    notes: str = ""

    @model_validator(mode="after")
    def require_service_consent_for_registration(self):
        if not self.service_consent:
            raise ValueError("義診服務使用必須獨立同意後才能建立掛號")
        return self


class ConsentRead(ConsentCreate):
    id: UUID
    patient_id: UUID
    consented_by: UUID | None = None
    withdrawn_at: datetime | None
    research_withdrawn_at: datetime | None = None
    withdrawn_by: UUID | None = None

    model_config = {"from_attributes": True}


class ConsentWithdraw(BaseModel):
    notes: str = ""
