from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.modules.audit_logs.service import write_audit_log
from app.modules.clinic_sessions.models import ClinicSession
from app.modules.patients.models import Patient
from app.modules.queue.models import QueueRecord
from app.modules.users.models import User
from app.modules.visits.models import Visit, VisitStatus
from app.modules.visits.schemas import VisitCreate

ALLOWED_TRANSITIONS: dict[VisitStatus, set[VisitStatus]] = {
    VisitStatus.REGISTERED: {VisitStatus.WAITING_FOR_CLINIC, VisitStatus.CANCELLED},
    VisitStatus.WAITING_FOR_CLINIC: {VisitStatus.IN_CONSULTATION, VisitStatus.CANCELLED},
    VisitStatus.IN_CONSULTATION: {
        VisitStatus.WAITING_FOR_PHARMACY,
        VisitStatus.COMPLETED,
        VisitStatus.CANCELLED,
    },
    VisitStatus.WAITING_FOR_PHARMACY: {VisitStatus.DISPENSING, VisitStatus.IN_CONSULTATION},
    VisitStatus.DISPENSING: {VisitStatus.WAITING_FOR_VERIFICATION, VisitStatus.IN_CONSULTATION},
    VisitStatus.WAITING_FOR_VERIFICATION: {VisitStatus.WAITING_FOR_PICKUP, VisitStatus.IN_CONSULTATION},
    VisitStatus.WAITING_FOR_PICKUP: {VisitStatus.COMPLETED},
    VisitStatus.COMPLETED: set(),
    VisitStatus.CANCELLED: set(),
}


def next_queue_number(db: Session, clinic_session_id) -> int:
    current = db.execute(
        select(func.max(Visit.queue_number)).where(Visit.clinic_session_id == clinic_session_id)
    ).scalar_one()
    return int(current or 0) + 1


def create_visit(db: Session, payload: VisitCreate) -> Visit:
    if db.get(ClinicSession, payload.clinic_session_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Clinic session not found")
    if db.get(Patient, payload.patient_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found")

    queue_number = next_queue_number(db, payload.clinic_session_id)
    visit = Visit(
        clinic_session_id=payload.clinic_session_id,
        patient_id=payload.patient_id,
        queue_number=queue_number,
        registered_at=datetime.now(timezone.utc),
        status=VisitStatus.REGISTERED,
        registration_staff=payload.registration_staff,
        notes=payload.notes,
    )
    queue_record = QueueRecord(
        clinic_session_id=payload.clinic_session_id,
        visit=visit,
        queue_number=queue_number,
    )
    db.add_all([visit, queue_record])
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Patient already has a visit in this clinic session",
        ) from exc
    db.refresh(visit)
    return visit


def update_visit_status(
    db: Session,
    visit: Visit,
    next_status: VisitStatus,
    *,
    actor: User | None = None,
    commit: bool = True,
) -> Visit:
    if next_status not in ALLOWED_TRANSITIONS[visit.status]:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Invalid visit status transition")
    previous_status = visit.status
    visit.status = next_status
    if next_status == VisitStatus.COMPLETED:
        visit.completed_at = datetime.now(timezone.utc)
    db.add(visit)
    write_audit_log(
        db,
        actor_user_id=actor.id if actor else None,
        action="visit.status_update",
        entity_type="visit",
        entity_id=visit.id,
        summary=f"{previous_status.value} -> {next_status.value}",
    )
    if commit:
        db.commit()
        db.refresh(visit)
    return visit
