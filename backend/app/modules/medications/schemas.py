from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class MedicationBase(BaseModel):
    code: str = Field(min_length=1, max_length=64)
    name: str = Field(min_length=1, max_length=160)
    generic_name: str = Field(default="", max_length=160)
    brand_name: str = Field(default="", max_length=160)
    dosage_form: str = Field(default="", max_length=80)
    strength: str = Field(default="", max_length=80)
    unit: str = Field(default="", max_length=40)
    route: str = Field(default="", max_length=80)
    manufacturer: str = Field(default="", max_length=160)
    notes: str = ""
    warnings: str = ""


class MedicationCreate(MedicationBase):
    is_active: bool = True


class MedicationUpdate(BaseModel):
    code: str | None = Field(default=None, min_length=1, max_length=64)
    name: str | None = Field(default=None, min_length=1, max_length=160)
    generic_name: str | None = Field(default=None, max_length=160)
    brand_name: str | None = Field(default=None, max_length=160)
    dosage_form: str | None = Field(default=None, max_length=80)
    strength: str | None = Field(default=None, max_length=80)
    unit: str | None = Field(default=None, max_length=40)
    route: str | None = Field(default=None, max_length=80)
    manufacturer: str | None = Field(default=None, max_length=160)
    notes: str | None = None
    warnings: str | None = None


class MedicationRead(MedicationBase):
    id: UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
