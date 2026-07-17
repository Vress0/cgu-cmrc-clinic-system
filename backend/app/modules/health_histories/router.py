from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.modules.auth.dependencies import require_permissions
from app.modules.health_histories.models import HealthHistory
from app.modules.health_histories.schemas import HealthHistoryRead, HealthHistoryUpsert
from app.modules.patients.models import Patient

router = APIRouter(prefix="/patients/{patient_id}/health-history", tags=["health_histories"])


@router.get("", response_model=HealthHistoryRead)
def get_health_history(
    patient_id: UUID,
    db: Session = Depends(get_db),
    _=Depends(require_permissions("patients:read")),
) -> HealthHistory:
    history = db.execute(
        select(HealthHistory).where(HealthHistory.patient_id == patient_id)
    ).scalar_one_or_none()
    if history is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="找不到健康背景資料")
    return history


@router.put("", response_model=HealthHistoryRead)
def upsert_health_history(
    patient_id: UUID,
    payload: HealthHistoryUpsert,
    db: Session = Depends(get_db),
    _=Depends(require_permissions("patients:write")),
) -> HealthHistory:
    if db.get(Patient, patient_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="找不到個案")
    history = db.execute(
        select(HealthHistory).where(HealthHistory.patient_id == patient_id)
    ).scalar_one_or_none()
    if history is None:
        history = HealthHistory(patient_id=patient_id, **payload.model_dump())
    else:
        for key, value in payload.model_dump().items():
            setattr(history, key, value)
    db.add(history)
    db.commit()
    db.refresh(history)
    return history
