from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.modules.auth.dependencies import require_permissions
from app.modules.users.models import User
from app.modules.vital_signs.models import VitalSign
from app.modules.vital_signs.schemas import VitalSignCreate, VitalSignRead, VitalSignUpdate
from app.modules.vital_signs.service import create_vital_sign, ensure_visit_exists, update_vital_sign

router = APIRouter(tags=["vital-signs"])


@router.get("/visits/{visit_id}/vital-signs", response_model=list[VitalSignRead])
def list_vital_signs(
    visit_id: UUID,
    db: Session = Depends(get_db),
    _=Depends(require_permissions("clinic:write")),
) -> list[VitalSign]:
    ensure_visit_exists(db, visit_id)
    statement = (
        select(VitalSign)
        .where(VitalSign.visit_id == visit_id)
        .order_by(VitalSign.measured_at.desc(), VitalSign.created_at.desc())
    )
    return list(db.execute(statement).scalars())


@router.post("/visits/{visit_id}/vital-signs", response_model=VitalSignRead, status_code=201)
def create_vital_sign_route(
    visit_id: UUID,
    payload: VitalSignCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions("clinic:write")),
) -> VitalSign:
    return create_vital_sign(db, visit_id, payload, current_user)


@router.get("/visits/{visit_id}/vital-signs/latest", response_model=VitalSignRead | None)
def get_latest_vital_sign(
    visit_id: UUID,
    db: Session = Depends(get_db),
    _=Depends(require_permissions("clinic:write")),
) -> VitalSign | None:
    ensure_visit_exists(db, visit_id)
    statement = (
        select(VitalSign)
        .where(VitalSign.visit_id == visit_id)
        .order_by(VitalSign.measured_at.desc(), VitalSign.created_at.desc())
        .limit(1)
    )
    return db.execute(statement).scalar_one_or_none()


@router.patch("/vital-signs/{vital_sign_id}", response_model=VitalSignRead)
def update_vital_sign_route(
    vital_sign_id: UUID,
    payload: VitalSignUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions("clinic:write")),
) -> VitalSign:
    vital_sign = db.get(VitalSign, vital_sign_id)
    if vital_sign is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vital sign not found")
    return update_vital_sign(db, vital_sign, payload, current_user)
