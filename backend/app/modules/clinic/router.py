from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.modules.auth.dependencies import require_permissions
from app.modules.clinic.schemas import ClinicQueueItem
from app.modules.clinic_sessions.models import ClinicSession
from app.modules.consultations.models import Consultation
from app.modules.patients.models import Patient
from app.modules.users.models import User
from app.modules.visits.models import Visit, VisitStatus
from app.modules.visits.service import update_visit_status
from app.modules.vital_signs.models import VitalSign

router = APIRouter(prefix="/clinic", tags=["clinic"])


def _queue_item(db: Session, visit: Visit, patient: Patient, clinic_session: ClinicSession) -> ClinicQueueItem:
    latest_vital_sign_at = db.execute(
        select(VitalSign.measured_at)
        .where(VitalSign.visit_id == visit.id)
        .order_by(VitalSign.measured_at.desc())
        .limit(1)
    ).scalar_one_or_none()
    has_consultation = (
        db.execute(select(Consultation.id).where(Consultation.visit_id == visit.id).limit(1)).scalar_one_or_none()
        is not None
    )
    return ClinicQueueItem(
        visit_id=visit.id,
        clinic_session_id=clinic_session.id,
        clinic_session_name=clinic_session.name,
        session_date=clinic_session.session_date,
        patient_id=patient.id,
        patient_case_number=patient.case_number,
        patient_name=patient.name,
        patient_sex=patient.sex,
        queue_number=visit.queue_number,
        status=visit.status,
        registered_at=visit.registered_at,
        notes=visit.notes,
        latest_vital_sign_at=latest_vital_sign_at,
        has_consultation=has_consultation,
    )


def get_visit_context(db: Session, visit_id: UUID) -> tuple[Visit, Patient, ClinicSession]:
    statement = (
        select(Visit, Patient, ClinicSession)
        .join(Patient, Patient.id == Visit.patient_id)
        .join(ClinicSession, ClinicSession.id == Visit.clinic_session_id)
        .where(Visit.id == visit_id)
    )
    row = db.execute(statement).one_or_none()
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Visit not found")
    return row


@router.get("/queue", response_model=list[ClinicQueueItem])
def get_clinic_queue(
    db: Session = Depends(get_db),
    _=Depends(require_permissions("clinic:write")),
) -> list[ClinicQueueItem]:
    active_statuses = [
        VisitStatus.REGISTERED,
        VisitStatus.WAITING_FOR_CLINIC,
        VisitStatus.IN_CONSULTATION,
        VisitStatus.WAITING_FOR_PHARMACY,
    ]
    statement = (
        select(Visit, Patient, ClinicSession)
        .join(Patient, Patient.id == Visit.patient_id)
        .join(ClinicSession, ClinicSession.id == Visit.clinic_session_id)
        .where(Visit.status.in_(active_statuses))
        .order_by(ClinicSession.session_date.desc(), Visit.queue_number.asc())
        .limit(100)
    )
    return [_queue_item(db, visit, patient, clinic_session) for visit, patient, clinic_session in db.execute(statement)]


@router.get("/queue/{visit_id}", response_model=ClinicQueueItem)
def get_clinic_queue_item(
    visit_id: UUID,
    db: Session = Depends(get_db),
    _=Depends(require_permissions("clinic:write")),
) -> ClinicQueueItem:
    visit, patient, clinic_session = get_visit_context(db, visit_id)
    return _queue_item(db, visit, patient, clinic_session)


@router.post("/queue/{visit_id}/start", response_model=ClinicQueueItem)
def start_consultation(
    visit_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions("clinic:write")),
) -> ClinicQueueItem:
    visit, patient, clinic_session = get_visit_context(db, visit_id)
    update_visit_status(db, visit, VisitStatus.IN_CONSULTATION, actor=current_user)
    return _queue_item(db, visit, patient, clinic_session)


@router.post("/queue/{visit_id}/cancel", response_model=ClinicQueueItem)
def cancel_consultation(
    visit_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions("clinic:write")),
) -> ClinicQueueItem:
    visit, patient, clinic_session = get_visit_context(db, visit_id)
    update_visit_status(db, visit, VisitStatus.CANCELLED, actor=current_user)
    return _queue_item(db, visit, patient, clinic_session)
