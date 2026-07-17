from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class ConsultationIntakeUpdate(BaseModel):
    chief_complaint: str = ""
    symptom_description: str = ""
    symptom_location: str = ""
    symptom_onset: str = ""
    symptom_duration: str = ""
    symptom_frequency: str = ""
    symptom_severity: str = ""
    worsening: str = ""
    previously_sought_care: str = ""
    previous_treatment: str = ""
    student_notes: str = ""


class ConsultationClinicalUpdate(BaseModel):
    clinical_findings: str = ""
    assessment_summary: str = ""
    treatment_recommendation: str = ""
    health_education: str = ""
    referral_recommendation: str = ""
    referral_urgency: str = ""
    follow_up_recommendation: str = ""
    requires_pharmacy: bool = False
    clinician_notes: str = ""
    inspection: str = ""
    auscultation_olfaction: str = ""
    inquiry: str = ""
    palpation: str = ""
    tongue_notes: str = ""
    pulse_notes: str = ""


class ConsultationComplete(BaseModel):
    requires_pharmacy: bool | None = None
    clinician_notes: str | None = Field(default=None, max_length=5000)


class ConsultationRead(ConsultationIntakeUpdate, ConsultationClinicalUpdate):
    id: UUID
    visit_id: UUID
    recorded_by: UUID | None
    recorded_at: datetime | None
    reviewed_by: UUID | None
    reviewed_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
