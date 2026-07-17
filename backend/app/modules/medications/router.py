from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.modules.audit_logs.service import write_audit_log
from app.modules.auth.dependencies import require_permissions
from app.modules.medications.models import Medication
from app.modules.medications.schemas import MedicationCreate, MedicationRead, MedicationUpdate
from app.modules.users.models import User

router = APIRouter(prefix="/medications", tags=["medications"])


@router.get("", response_model=list[MedicationRead])
def list_medications(
    q: str = "",
    active_only: bool = Query(default=False),
    db: Session = Depends(get_db),
    _=Depends(require_permissions("clinic:write")),
) -> list[Medication]:
    statement = select(Medication).order_by(Medication.name.asc())
    if q:
        keyword = f"%{q.strip()}%"
        statement = statement.where(
            or_(
                Medication.code.ilike(keyword),
                Medication.name.ilike(keyword),
                Medication.generic_name.ilike(keyword),
                Medication.brand_name.ilike(keyword),
            )
        )
    if active_only:
        statement = statement.where(Medication.is_active.is_(True))
    return list(db.execute(statement.limit(200)).scalars())


@router.post("", response_model=MedicationRead, status_code=201)
def create_medication(
    payload: MedicationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions("inventory:manage")),
) -> Medication:
    medication = Medication(**payload.model_dump())
    db.add(medication)
    write_audit_log(
        db,
        actor_user_id=current_user.id,
        action="medication.create",
        entity_type="medication",
        entity_id=medication.id,
        summary=f"Created medication {payload.code}",
    )
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Medication code already exists") from exc
    db.refresh(medication)
    return medication


@router.patch("/{medication_id}", response_model=MedicationRead)
def update_medication(
    medication_id: UUID,
    payload: MedicationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions("inventory:manage")),
) -> Medication:
    medication = db.get(Medication, medication_id)
    if medication is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Medication not found")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(medication, key, value)
    write_audit_log(
        db,
        actor_user_id=current_user.id,
        action="medication.update",
        entity_type="medication",
        entity_id=medication.id,
        summary=f"Updated medication {medication.code}",
    )
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Medication code already exists") from exc
    db.refresh(medication)
    return medication


@router.post("/{medication_id}/activate", response_model=MedicationRead)
def activate_medication(
    medication_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions("inventory:manage")),
) -> Medication:
    return set_medication_active(db, medication_id, True, current_user)


@router.post("/{medication_id}/deactivate", response_model=MedicationRead)
def deactivate_medication(
    medication_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions("inventory:manage")),
) -> Medication:
    return set_medication_active(db, medication_id, False, current_user)


def set_medication_active(db: Session, medication_id: UUID, is_active: bool, actor: User) -> Medication:
    medication = db.get(Medication, medication_id)
    if medication is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Medication not found")
    medication.is_active = is_active
    write_audit_log(
        db,
        actor_user_id=actor.id,
        action="medication.activate" if is_active else "medication.deactivate",
        entity_type="medication",
        entity_id=medication.id,
        summary=f"{'Activated' if is_active else 'Deactivated'} medication {medication.code}",
    )
    db.commit()
    db.refresh(medication)
    return medication
