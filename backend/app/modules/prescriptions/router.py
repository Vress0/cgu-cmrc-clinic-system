from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.modules.auth.dependencies import require_permissions
from app.modules.prescriptions.models import Prescription
from app.modules.prescriptions.schemas import (
    PrescriptionCreate,
    PrescriptionItemCreate,
    PrescriptionItemUpdate,
    PrescriptionRead,
    PrescriptionVoid,
)
from app.modules.prescriptions.service import (
    add_item,
    confirm_prescription,
    get_or_create_prescription,
    get_prescription,
    remove_item,
    send_to_pharmacy,
    update_item,
    void_prescription,
)
from app.modules.users.models import User

router = APIRouter(tags=["prescriptions"])


@router.get("/visits/{visit_id}/prescription", response_model=PrescriptionRead)
def get_visit_prescription(
    visit_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions("clinic:write")),
) -> Prescription:
    prescription = get_or_create_prescription(db, visit_id, current_user)
    db.commit()
    return get_prescription(db, prescription.id)


@router.post("/visits/{visit_id}/prescription", response_model=PrescriptionRead, status_code=201)
def create_visit_prescription(
    visit_id: UUID,
    _: PrescriptionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions("clinic:write")),
) -> Prescription:
    prescription = get_or_create_prescription(db, visit_id, current_user)
    db.commit()
    return get_prescription(db, prescription.id)


@router.post("/prescriptions/{prescription_id}/items", response_model=PrescriptionRead, status_code=201)
def post_prescription_item(
    prescription_id: UUID,
    payload: PrescriptionItemCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions("clinic:write")),
) -> Prescription:
    return add_item(db, prescription_id, payload, current_user)


@router.patch("/prescription-items/{item_id}", response_model=PrescriptionRead)
def patch_prescription_item(
    item_id: UUID,
    payload: PrescriptionItemUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions("clinic:write")),
) -> Prescription:
    return update_item(db, item_id, payload, current_user)


@router.delete("/prescription-items/{item_id}", response_model=PrescriptionRead)
def delete_prescription_item(
    item_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions("clinic:write")),
) -> Prescription:
    return remove_item(db, item_id, current_user)


@router.post("/prescriptions/{prescription_id}/confirm", response_model=PrescriptionRead)
def post_prescription_confirm(
    prescription_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions("prescriptions:confirm")),
) -> Prescription:
    return confirm_prescription(db, prescription_id, current_user)


@router.post("/prescriptions/{prescription_id}/send-to-pharmacy", response_model=PrescriptionRead)
def post_prescription_send_to_pharmacy(
    prescription_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions("prescriptions:confirm")),
) -> Prescription:
    return send_to_pharmacy(db, prescription_id, current_user)


@router.post("/prescriptions/{prescription_id}/void", response_model=PrescriptionRead)
def post_prescription_void(
    prescription_id: UUID,
    payload: PrescriptionVoid,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions("prescriptions:confirm")),
) -> Prescription:
    return void_prescription(db, prescription_id, payload.reason, current_user)
