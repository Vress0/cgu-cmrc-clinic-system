from datetime import datetime, timezone

from fastapi import APIRouter
from pydantic import BaseModel

from app.db.session import check_database

router = APIRouter()


class HealthResponse(BaseModel):
    status: str
    database: str
    service: str
    version: str
    checked_at: datetime


@router.get("/health", response_model=HealthResponse)
def health_check() -> HealthResponse:
    database_status = "ok" if check_database() else "unavailable"
    service_status = "ok" if database_status == "ok" else "degraded"

    return HealthResponse(
        status=service_status,
        database=database_status,
        service="backend",
        version="0.1.0",
        checked_at=datetime.now(timezone.utc),
    )
