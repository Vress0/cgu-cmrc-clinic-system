from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.modules.auth.dependencies import require_permissions
from app.modules.users.models import User
from app.modules.visits.models import Visit, VisitStatus
from app.modules.visits.schemas import VisitCreate, VisitRead, VisitStatusUpdate
from app.modules.visits.service import create_visit, update_visit_status

router = APIRouter(prefix="/visits", tags=["visits"])


@router.get("", response_model=list[VisitRead])
def list_visits(
    clinic_session_id: UUID | None = None,
    status_filter: VisitStatus | None = Query(default=None, alias="status"),
    db: Session = Depends(get_db),
    _=Depends(require_permissions("visits:manage")),
) -> list[Visit]:
    statement = select(Visit).order_by(Visit.queue_number.asc())
    if clinic_session_id:
        statement = statement.where(Visit.clinic_session_id == clinic_session_id)
    if status_filter:
        statement = statement.where(Visit.status == status_filter)
    return list(db.execute(statement.limit(100)).scalars())


@router.post("", response_model=VisitRead, status_code=201)
def create_visit_route(
    payload: VisitCreate,
    db: Session = Depends(get_db),
    _=Depends(require_permissions("visits:manage")),
) -> Visit:
    return create_visit(db, payload)


@router.patch("/{visit_id}/status", response_model=VisitRead)
def patch_visit_status(
    visit_id: UUID,
    payload: VisitStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions("visits:manage")),
) -> Visit:
    visit = db.get(Visit, visit_id)
    if visit is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Visit not found")
    return update_visit_status(db, visit, payload.status, actor=current_user)
