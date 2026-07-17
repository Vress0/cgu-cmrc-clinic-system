from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.modules.auth.dependencies import require_permissions
from app.modules.clinic_sessions.models import ClinicSession
from app.modules.clinic_sessions.schemas import ClinicSessionCreate, ClinicSessionRead

router = APIRouter(prefix="/clinic-sessions", tags=["clinic_sessions"])


@router.get("", response_model=list[ClinicSessionRead])
def list_clinic_sessions(
    db: Session = Depends(get_db),
    _=Depends(require_permissions("sessions:manage")),
) -> list[ClinicSession]:
    return list(db.execute(select(ClinicSession).order_by(ClinicSession.session_date.desc())).scalars())


@router.post("", response_model=ClinicSessionRead, status_code=201)
def create_clinic_session(
    payload: ClinicSessionCreate,
    db: Session = Depends(get_db),
    _=Depends(require_permissions("sessions:manage")),
) -> ClinicSession:
    session = ClinicSession(**payload.model_dump())
    db.add(session)
    db.commit()
    db.refresh(session)
    return session
