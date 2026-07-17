from datetime import datetime, timezone
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.modules.audit_logs.service import write_audit_log
from app.modules.consultations.models import Consultation
from app.modules.consultations.schemas import (
    ConsultationClinicalUpdate,
    ConsultationComplete,
    ConsultationIntakeUpdate,
)
from app.modules.users.models import User
from app.modules.visits.models import Visit, VisitStatus
from app.modules.visits.service import update_visit_status


def get_visit_or_404(db: Session, visit_id: UUID) -> Visit:
    visit = db.get(Visit, visit_id)
    if visit is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Visit not found")
    return visit


def get_or_create_consultation(db: Session, visit: Visit) -> Consultation:
    if visit.consultation is not None:
        return visit.consultation
    consultation = Consultation(visit_id=visit.id)
    db.add(consultation)
    db.flush()
    return consultation


def ensure_in_consultation(visit: Visit) -> None:
    if visit.status != VisitStatus.IN_CONSULTATION:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Visit is not in consultation")


def update_intake(db: Session, visit_id: UUID, payload: ConsultationIntakeUpdate, actor: User) -> Consultation:
    visit = get_visit_or_404(db, visit_id)
    ensure_in_consultation(visit)
    consultation = get_or_create_consultation(db, visit)
    for key, value in payload.model_dump().items():
        setattr(consultation, key, value)
    consultation.recorded_by = actor.id
    consultation.recorded_at = datetime.now(timezone.utc)
    write_audit_log(
        db,
        actor_user_id=actor.id,
        action="consultation.intake_update",
        entity_type="consultation",
        entity_id=consultation.id,
        summary=f"Updated intake for visit {visit.id}",
    )
    db.commit()
    db.refresh(consultation)
    return consultation


def update_clinical(db: Session, visit_id: UUID, payload: ConsultationClinicalUpdate, actor: User) -> Consultation:
    visit = get_visit_or_404(db, visit_id)
    ensure_in_consultation(visit)
    consultation = get_or_create_consultation(db, visit)
    for key, value in payload.model_dump().items():
        setattr(consultation, key, value)
    consultation.reviewed_by = actor.id
    consultation.reviewed_at = datetime.now(timezone.utc)
    write_audit_log(
        db,
        actor_user_id=actor.id,
        action="consultation.clinical_update",
        entity_type="consultation",
        entity_id=consultation.id,
        summary=f"Updated clinical record for visit {visit.id}",
    )
    db.commit()
    db.refresh(consultation)
    return consultation


def complete_consultation(db: Session, visit_id: UUID, payload: ConsultationComplete, actor: User) -> Consultation:
    visit = get_visit_or_404(db, visit_id)
    ensure_in_consultation(visit)
    consultation = get_or_create_consultation(db, visit)
    if payload.requires_pharmacy is not None:
        consultation.requires_pharmacy = payload.requires_pharmacy
    if payload.clinician_notes is not None:
        consultation.clinician_notes = payload.clinician_notes
    if consultation.requires_pharmacy:
        from app.modules.prescriptions.service import consultation_requires_confirmed_prescription

        if consultation_requires_confirmed_prescription(db, visit.id):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Confirmed prescription is required before sending this visit to pharmacy",
            )
    consultation.reviewed_by = actor.id
    consultation.reviewed_at = datetime.now(timezone.utc)
    next_status = VisitStatus.WAITING_FOR_PHARMACY if consultation.requires_pharmacy else VisitStatus.COMPLETED
    update_visit_status(db, visit, next_status, actor=actor, commit=False)
    write_audit_log(
        db,
        actor_user_id=actor.id,
        action="consultation.complete",
        entity_type="visit",
        entity_id=visit.id,
        summary=f"Completed consultation with status {next_status.value}",
    )
    db.commit()
    db.refresh(consultation)
    return consultation
