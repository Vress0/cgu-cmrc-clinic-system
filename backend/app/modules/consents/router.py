from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.modules.audit_logs.service import write_audit_log
from app.modules.auth.dependencies import require_permissions
from app.modules.consents.models import Consent
from app.modules.consents.schemas import ConsentCreate, ConsentRead, ConsentWithdraw
from app.modules.patients.models import Patient
from app.modules.users.models import User

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
    current_user: User = Depends(require_permissions("patients:write")),
) -> Consent:
    if db.get(Patient, patient_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found")
    consent = Consent(patient_id=patient_id, consented_by=current_user.id, **payload.model_dump())
    db.add(consent)
    db.flush()
    write_audit_log(
        db,
        actor_user_id=current_user.id,
        action="CONSENT_CREATED",
        entity_type="consent",
        entity_id=consent.id,
        summary=f"Created consent for patient {patient_id}",
    )
    db.commit()
    db.refresh(consent)
    return consent


@router.post("/{consent_id}/withdraw-research", response_model=ConsentRead)
def withdraw_research_consent(
    patient_id: UUID,
    consent_id: UUID,
    payload: ConsentWithdraw,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions("patients:write")),
) -> Consent:
    consent = db.get(Consent, consent_id)
    if consent is None or consent.patient_id != patient_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Consent not found")
    if not consent.research_consent:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Research consent was not granted")
    if consent.research_withdrawn_at is not None:
        return consent
    consent.research_consent = False
    consent.research_withdrawn_at = datetime.now(timezone.utc)
    consent.withdrawn_at = consent.research_withdrawn_at
    consent.withdrawn_by = current_user.id
    if payload.notes:
        consent.notes = f"{consent.notes}\n{payload.notes}".strip()
    write_audit_log(
        db,
        actor_user_id=current_user.id,
        action="CONSENT_RESEARCH_WITHDRAWN",
        entity_type="consent",
        entity_id=consent.id,
        summary=f"Withdrew research consent for patient {patient_id}",
    )
    db.commit()
    db.refresh(consent)
    return consent
