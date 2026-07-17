from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.modules.auth.dependencies import require_permissions
from app.modules.consents.models import Consent
from app.modules.consents.schemas import ConsentCreate, ConsentRead
from app.modules.patients.models import Patient

router = APIRouter(prefix="/patients/{patient_id}/consents", tags=["consents"])


@router.get("", response_model=list[ConsentRead])
def list_consents(
    patient_id: UUID,
    db: Session = Depends(get_db),
    _=Depends(require_permissions("patients:read")),
) -> list[Consent]:
    return list(
        db.execute(
            select(Consent).where(Consent.patient_id == patient_id).order_by(Consent.consented_at.desc())
        ).scalars()
    )


@router.post("", response_model=ConsentRead, status_code=201)
def create_consent(
    patient_id: UUID,
    payload: ConsentCreate,
    db: Session = Depends(get_db),
    _=Depends(require_permissions("patients:write")),
) -> Consent:
    if db.get(Patient, patient_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="找不到個案")
    consent = Consent(patient_id=patient_id, **payload.model_dump())
    db.add(consent)
    db.commit()
    db.refresh(consent)
    return consent
