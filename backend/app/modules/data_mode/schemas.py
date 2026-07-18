from pydantic import BaseModel, Field

from app.core.data_mode import DataMode


class DataModeStatus(BaseModel):
    mode: DataMode
    label: str
    can_switch: bool
    enable_demo_mode: bool
    can_access_live: bool
    can_access_demo: bool


class DataModeSwitchRequest(BaseModel):
    mode: DataMode
    confirmation: str = Field(min_length=1, max_length=80)


class DataModeSwitchResponse(DataModeStatus):
    message: str


class DemoDataStatus(BaseModel):
    enabled: bool
    patient_count: int
    session_count: int
    visit_count: int
    prescription_count: int
    inventory_batch_count: int
    audit_log_count: int


class DemoDataActionRequest(BaseModel):
    confirmation: str = Field(default="", max_length=80)
