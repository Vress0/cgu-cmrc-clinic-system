from datetime import datetime, timezone
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.modules.audit_logs.service import write_audit_log
from app.modules.consultations.models import Consultation
from app.modules.medications.models import Medication
from app.modules.prescriptions.models import Prescription, PrescriptionItem, PrescriptionStatus
from app.modules.prescriptions.schemas import PrescriptionItemCreate, PrescriptionItemUpdate
from app.modules.users.models import User
from app.modules.visits.models import Visit, VisitStatus
from app.modules.visits.service import update_visit_status

EDITABLE_STATUSES = {PrescriptionStatus.DRAFT, PrescriptionStatus.RETURNED_TO_CLINIC}


def get_visit_or_404(db: Session, visit_id: UUID) -> Visit:
    visit = db.get(Visit, visit_id)
    if visit is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Visit not found")
    return visit


def get_prescription(db: Session, prescription_id: UUID) -> Prescription:
    prescription = db.execute(
        select(Prescription)
        .where(Prescription.id == prescription_id)
        .options(selectinload(Prescription.items).selectinload(PrescriptionItem.medication))
    ).scalar_one_or_none()
    if prescription is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Prescription not found")
    return prescription


def get_or_create_prescription(db: Session, visit_id: UUID, actor: User | None = None) -> Prescription:
    visit = get_visit_or_404(db, visit_id)
    prescription = db.execute(
        select(Prescription)
        .where(Prescription.visit_id == visit.id)
        .options(selectinload(Prescription.items).selectinload(PrescriptionItem.medication))
    ).scalar_one_or_none()
    if prescription is not None:
        return prescription
    prescription = Prescription(visit_id=visit.id, created_by=actor.id if actor else None)
    db.add(prescription)
    db.flush()
    write_audit_log(
        db,
        actor_user_id=actor.id if actor else None,
        action="prescription.create",
        entity_type="prescription",
        entity_id=prescription.id,
        summary=f"Created prescription for visit {visit.id}",
    )
    return prescription


def ensure_editable(prescription: Prescription) -> None:
    if prescription.status not in EDITABLE_STATUSES:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Prescription cannot be edited in this status")


def ensure_has_items(prescription: Prescription) -> None:
    if not prescription.items:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Prescription must contain at least one item")


def get_active_medication(db: Session, medication_id: UUID) -> Medication:
    medication = db.get(Medication, medication_id)
    if medication is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Medication not found")
    if not medication.is_active:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Inactive medication cannot be prescribed")
    return medication


def add_item(
    db: Session,
    prescription_id: UUID,
    payload: PrescriptionItemCreate,
    actor: User,
) -> Prescription:
    prescription = get_prescription(db, prescription_id)
    ensure_editable(prescription)
    get_active_medication(db, payload.medication_id)
    item = PrescriptionItem(prescription_id=prescription.id, **payload.model_dump())
    prescription.version += 1
    db.add(item)
    write_audit_log(
        db,
        actor_user_id=actor.id,
        action="prescription.item_add",
        entity_type="prescription",
        entity_id=prescription.id,
        summary=f"Added medication item to prescription {prescription.id}",
    )
    db.commit()
    return get_prescription(db, prescription.id)


def update_item(
    db: Session,
    item_id: UUID,
    payload: PrescriptionItemUpdate,
    actor: User,
) -> Prescription:
    item = db.get(PrescriptionItem, item_id)
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Prescription item not found")
    prescription = get_prescription(db, item.prescription_id)
    ensure_editable(prescription)
    values = payload.model_dump(exclude_unset=True)
    if "medication_id" in values and values["medication_id"] is not None:
        get_active_medication(db, values["medication_id"])
    for key, value in values.items():
        setattr(item, key, value)
    prescription.version += 1
    write_audit_log(
        db,
        actor_user_id=actor.id,
        action="prescription.item_update",
        entity_type="prescription",
        entity_id=prescription.id,
        summary=f"Updated medication item {item.id}",
    )
    db.commit()
    return get_prescription(db, prescription.id)


def remove_item(db: Session, item_id: UUID, actor: User) -> Prescription:
    item = db.get(PrescriptionItem, item_id)
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Prescription item not found")
    prescription = get_prescription(db, item.prescription_id)
    ensure_editable(prescription)
    prescription.version += 1
    db.delete(item)
    write_audit_log(
        db,
        actor_user_id=actor.id,
        action="prescription.item_remove",
        entity_type="prescription",
        entity_id=prescription.id,
        summary=f"Removed medication item {item.id}",
    )
    db.commit()
    return get_prescription(db, prescription.id)


def confirm_prescription(db: Session, prescription_id: UUID, actor: User) -> Prescription:
    prescription = get_prescription(db, prescription_id)
    if prescription.status not in EDITABLE_STATUSES:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Prescription is not ready to confirm")
    ensure_has_items(prescription)
    prescription.status = PrescriptionStatus.CONFIRMED
    prescription.confirmed_by = actor.id
    prescription.confirmed_at = datetime.now(timezone.utc)
    write_audit_log(
        db,
        actor_user_id=actor.id,
        action="prescription.confirm",
        entity_type="prescription",
        entity_id=prescription.id,
        summary=f"Confirmed prescription {prescription.id}",
    )
    db.commit()
    return get_prescription(db, prescription.id)


def send_to_pharmacy(db: Session, prescription_id: UUID, actor: User) -> Prescription:
    prescription = get_prescription(db, prescription_id)
    if prescription.status != PrescriptionStatus.CONFIRMED:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Prescription must be confirmed before sending")
    ensure_has_items(prescription)
    visit = get_visit_or_404(db, prescription.visit_id)
    prescription.status = PrescriptionStatus.SENT_TO_PHARMACY
    prescription.sent_to_pharmacy_at = datetime.now(timezone.utc)
    if visit.status == VisitStatus.IN_CONSULTATION:
        update_visit_status(db, visit, VisitStatus.WAITING_FOR_PHARMACY, actor=actor, commit=False)
    elif visit.status != VisitStatus.WAITING_FOR_PHARMACY:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Visit is not ready for pharmacy")
    write_audit_log(
        db,
        actor_user_id=actor.id,
        action="prescription.send_to_pharmacy",
        entity_type="prescription",
        entity_id=prescription.id,
        summary=f"Sent prescription {prescription.id} to pharmacy",
    )
    db.commit()
    return get_prescription(db, prescription.id)


def void_prescription(db: Session, prescription_id: UUID, reason: str, actor: User) -> Prescription:
    prescription = get_prescription(db, prescription_id)
    if prescription.status == PrescriptionStatus.SENT_TO_PHARMACY:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Sent prescription cannot be voided here")
    if prescription.status == PrescriptionStatus.VOIDED:
        return prescription
    prescription.status = PrescriptionStatus.VOIDED
    prescription.voided_at = datetime.now(timezone.utc)
    prescription.void_reason = reason
    write_audit_log(
        db,
        actor_user_id=actor.id,
        action="prescription.void",
        entity_type="prescription",
        entity_id=prescription.id,
        summary=f"Voided prescription {prescription.id}",
    )
    db.commit()
    return get_prescription(db, prescription.id)


def consultation_requires_confirmed_prescription(db: Session, visit_id: UUID) -> bool:
    consultation = db.execute(select(Consultation).where(Consultation.visit_id == visit_id)).scalar_one_or_none()
    if consultation is None or not consultation.requires_pharmacy:
        return False
    prescription = db.execute(select(Prescription).where(Prescription.visit_id == visit_id)).scalar_one_or_none()
    return prescription is None or prescription.status not in {
        PrescriptionStatus.CONFIRMED,
        PrescriptionStatus.SENT_TO_PHARMACY,
    }
