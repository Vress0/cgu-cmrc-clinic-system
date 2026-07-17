from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field, model_validator

from app.modules.vital_signs.models import BloodGlucoseContext


class VitalSignBase(BaseModel):
    systolic_blood_pressure: int | None = Field(default=None, ge=40, le=260)
    diastolic_blood_pressure: int | None = Field(default=None, ge=30, le=160)
    pulse: int | None = Field(default=None, ge=20, le=240)
    temperature: Decimal | None = Field(default=None, ge=30, le=45)
    oxygen_saturation: int | None = Field(default=None, ge=50, le=100)
    height_cm: Decimal | None = Field(default=None, ge=30, le=250)
    weight_kg: Decimal | None = Field(default=None, ge=2, le=300)
    bmi: Decimal | None = Field(default=None, ge=5, le=80)
    blood_glucose: Decimal | None = Field(default=None, ge=0, le=1000)
    blood_glucose_context: BloodGlucoseContext | None = None
    notes: str = ""

    @model_validator(mode="after")
    def validate_blood_pressure(self):
        if (
            self.systolic_blood_pressure is not None
            and self.diastolic_blood_pressure is not None
            and self.systolic_blood_pressure <= self.diastolic_blood_pressure
        ):
            raise ValueError("systolic blood pressure must be greater than diastolic blood pressure")
        return self


class VitalSignCreate(VitalSignBase):
    measured_at: datetime | None = None


class VitalSignUpdate(BaseModel):
    systolic_blood_pressure: int | None = Field(default=None, ge=40, le=260)
    diastolic_blood_pressure: int | None = Field(default=None, ge=30, le=160)
    pulse: int | None = Field(default=None, ge=20, le=240)
    temperature: Decimal | None = Field(default=None, ge=30, le=45)
    oxygen_saturation: int | None = Field(default=None, ge=50, le=100)
    height_cm: Decimal | None = Field(default=None, ge=30, le=250)
    weight_kg: Decimal | None = Field(default=None, ge=2, le=300)
    bmi: Decimal | None = Field(default=None, ge=5, le=80)
    blood_glucose: Decimal | None = Field(default=None, ge=0, le=1000)
    blood_glucose_context: BloodGlucoseContext | None = None
    notes: str | None = None
    measured_at: datetime | None = None

    @model_validator(mode="after")
    def validate_blood_pressure(self):
        if (
            self.systolic_blood_pressure is not None
            and self.diastolic_blood_pressure is not None
            and self.systolic_blood_pressure <= self.diastolic_blood_pressure
        ):
            raise ValueError("systolic blood pressure must be greater than diastolic blood pressure")
        return self


class VitalSignRead(VitalSignBase):
    id: UUID
    visit_id: UUID
    measured_by: UUID
    measured_at: datetime
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
