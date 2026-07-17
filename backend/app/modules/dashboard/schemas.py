from decimal import Decimal

from pydantic import BaseModel


class DashboardSummary(BaseModel):
    registered: int
    waiting_for_clinic: int
    in_consultation: int
    waiting_for_pharmacy: int
    dispensing: int
    waiting_for_verification: int
    waiting_for_pickup: int
    completed: int
    cancelled: int
    active_sessions: int
    patient_count: int
    medication_count: int
    inventory_available: Decimal
    low_stock_count: int
    expiring_count: int
    expired_count: int
