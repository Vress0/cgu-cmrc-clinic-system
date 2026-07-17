from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.modules.audit_logs.service import write_audit_log
from app.modules.users.models import User
from app.modules.visits.models import Visit
from app.modules.vital_signs.models import VitalSign
from app.modules.vital_signs.schemas import VitalSignCreate, VitalSignUpdate


def calculate_bmi(height_cm: Decimal | float | None, weight_kg: Decimal | float | None) -> Decimal | None:
    if height_cm is None or weight_kg is None:
        return None
    height_m = Decimal(str(height_cm)) / Decimal("100")
    if height_m <= 0:
        return None
    bmi = Decimal(str(weight_kg)) / (height_m * height_m)
    return bmi.quantize(Decimal("0.01"))


def ensure_visit_exists(db: Session, visit_id: UUID) -> Visit:
    visit = db.get(Visit, visit_id)
    if visit is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Visit not found")
    return visit


def create_vital_sign(db: Session, visit_id: UUID, payload: VitalSignCreate, actor: User) -> VitalSign:
    ensure_visit_exists(db, visit_id)
    values = payload.model_dump()
    if values.get("bmi") is None:
        values["bmi"] = calculate_bmi(values.get("height_cm"), values.get("weight_kg"))
    vital_sign = VitalSign(
        visit_id=visit_id,
        measured_by=actor.id,
        measured_at=payload.measured_at or datetime.now(timezone.utc),
        **{key: value for key, value in values.items() if key != "measured_at"},
    )
    db.add(vital_sign)
    db.flush()
    write_audit_log(
        db,
        actor_user_id=actor.id,
        action="vital_sign.create",
        entity_type="vital_sign",
        entity_id=vital_sign.id,
        summary=f"Recorded vital signs for visit {visit_id}",
    )
    db.commit()
    db.refresh(vital_sign)
    return vital_sign


def update_vital_sign(db: Session, vital_sign: VitalSign, payload: VitalSignUpdate, actor: User) -> VitalSign:
    values = payload.model_dump(exclude_unset=True)
    for key, value in values.items():
        setattr(vital_sign, key, value)
    if ("height_cm" in values or "weight_kg" in values) and "bmi" not in values:
        vital_sign.bmi = calculate_bmi(vital_sign.height_cm, vital_sign.weight_kg)
    db.add(vital_sign)
    write_audit_log(
        db,
        actor_user_id=actor.id,
        action="vital_sign.update",
        entity_type="vital_sign",
        entity_id=vital_sign.id,
        summary=f"Updated vital signs for visit {vital_sign.visit_id}",
    )
    db.commit()
    db.refresh(vital_sign)
    return vital_sign
