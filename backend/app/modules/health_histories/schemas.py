from uuid import UUID

from pydantic import BaseModel


class HealthHistoryUpsert(BaseModel):
    chronic_diseases: str = ""
    allergies: str = ""
    current_medications: str = ""
    surgery_history: str = ""
    fall_history: str = ""
    smoking_status: str = ""
    alcohol_status: str = ""
    sleep_status: str = ""
    diet_status: str = ""
    notes: str = ""


class HealthHistoryRead(HealthHistoryUpsert):
    id: UUID
    patient_id: UUID

    model_config = {"from_attributes": True}
