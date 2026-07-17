from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.modules.audit_logs.service import write_audit_log
from app.modules.clinic_sessions.models import ClinicSession
from app.modules.dispensing.models import DispensingItem, DispensingRecord, DispensingStatus
from app.modules.dispensing.schemas import (
    DispensingHandOut,
    DispensingItemsUpdate,
    DispensingReturn,
    DispensingVerify,
    PharmacyQueueItem,
    PharmacyVisitDetail,
)
from app.modules.patients.models import Patient
from app.modules.prescriptions.models import Prescription, PrescriptionItem, PrescriptionStatus
from app.modules.users.models import User
from app.modules.visits.models import Visit, VisitStatus
from app.modules.visits.service import update_visit_status

ACTIVE_DISPENSING_STATUSES = {
    DispensingStatus.PENDING,
    DispensingStatus.IN_PROGRESS,
    DispensingStatus.WAITING_FOR_VERIFICATION,
    DispensingStatus.VERIFIED,
    DispensingStatus.WAITING_FOR_PICKUP,
}


def is_admin(user: User) -> bool:
    return any(role.name == "admin" for role in user.roles)


def get_dispensing_record(db: Session, dispensing_id: UUID) -> DispensingRecord:
    record = db.execute(
        select(DispensingRecord)
        .where(DispensingRecord.id == dispensing_id)
        .options(
            selectinload(DispensingRecord.items).selectinload(DispensingItem.medication),
            selectinload(DispensingRecord.items)
            .selectinload(DispensingItem.prescription_item)
            .selectinload(PrescriptionItem.medication),
        )
    ).scalar_one_or_none()
    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dispensing record not found")
    return record


def get_prescription(db: Session, prescription_id: UUID) -> Prescription:
    prescription = db.execute(
        select(Prescription)
        .where(Prescription.id == prescription_id)
        .options(selectinload(Prescription.items).selectinload(PrescriptionItem.medication))
    ).scalar_one_or_none()
    if prescription is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Prescription not found")
    return prescription


def active_record_for_prescription(db: Session, prescription_id: UUID) -> DispensingRecord | None:
    return db.execute(
        select(DispensingRecord)
        .where(
            DispensingRecord.prescription_id == prescription_id,
            DispensingRecord.status.in_(ACTIVE_DISPENSING_STATUSES),
        )
        .limit(1)
    ).scalar_one_or_none()


def get_visit_context(db: Session, visit_id: UUID) -> tuple[Visit, Patient, ClinicSession, Prescription]:
    row = db.execute(
        select(Visit, Patient, ClinicSession, Prescription)
        .join(Patient, Patient.id == Visit.patient_id)
        .join(ClinicSession, ClinicSession.id == Visit.clinic_session_id)
        .join(Prescription, Prescription.visit_id == Visit.id)
        .where(Visit.id == visit_id)
    ).one_or_none()
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pharmacy visit not found")
    return row


def latest_record_for_prescription(db: Session, prescription_id: UUID) -> DispensingRecord | None:
    return db.execute(
        select(DispensingRecord)
        .where(DispensingRecord.prescription_id == prescription_id)
        .order_by(DispensingRecord.created_at.desc())
        .limit(1)
    ).scalar_one_or_none()


def build_queue_item(
    db: Session,
    visit: Visit,
    patient: Patient,
    clinic_session: ClinicSession,
    prescription: Prescription,
) -> PharmacyQueueItem:
    record = latest_record_for_prescription(db, prescription.id)
    item_count, total_quantity = db.execute(
        select(func.count(PrescriptionItem.id), func.coalesce(func.sum(PrescriptionItem.quantity), 0))
        .where(PrescriptionItem.prescription_id == prescription.id)
    ).one()
    return PharmacyQueueItem(
        visit_id=visit.id,
        clinic_session_id=clinic_session.id,
        clinic_session_name=clinic_session.name,
        session_date=clinic_session.session_date,
        patient_id=patient.id,
        patient_case_number=patient.case_number,
        patient_name=patient.name,
        patient_sex=patient.sex,
        queue_number=visit.queue_number,
        visit_status=visit.status,
        prescription_id=prescription.id,
        prescription_status=prescription.status.value,
        dispensing_id=record.id if record else None,
        dispensing_status=record.status if record else None,
        item_count=int(item_count or 0),
        total_quantity=Decimal(total_quantity or 0),
        assigned_to=record.assigned_to if record else None,
        started_at=record.started_at if record else None,
        prepared_at=record.prepared_at if record else None,
        verified_at=record.verified_at if record else None,
        handed_out_at=record.handed_out_at if record else None,
        notes=visit.notes,
    )


def list_pharmacy_queue(
    db: Session,
    *,
    session_id: UUID | None = None,
    status_filter: str | None = None,
    search: str = "",
) -> list[PharmacyQueueItem]:
    statement = (
        select(Visit, Patient, ClinicSession, Prescription)
        .join(Patient, Patient.id == Visit.patient_id)
        .join(ClinicSession, ClinicSession.id == Visit.clinic_session_id)
        .join(Prescription, Prescription.visit_id == Visit.id)
        .where(
            or_(
                Visit.status.in_(
                    [
                        VisitStatus.WAITING_FOR_PHARMACY,
                        VisitStatus.DISPENSING,
                        VisitStatus.WAITING_FOR_VERIFICATION,
                        VisitStatus.WAITING_FOR_PICKUP,
                    ]
                ),
                Prescription.status.in_(
                    [
                        PrescriptionStatus.SENT_TO_PHARMACY,
                        PrescriptionStatus.DISPENSING,
                        PrescriptionStatus.WAITING_FOR_VERIFICATION,
                        PrescriptionStatus.VERIFIED,
                        PrescriptionStatus.WAITING_FOR_PICKUP,
                    ]
                ),
            )
        )
        .order_by(ClinicSession.session_date.desc(), Visit.queue_number.asc())
        .limit(200)
    )
    if session_id:
        statement = statement.where(Visit.clinic_session_id == session_id)
    if search:
        keyword = f"%{search.strip()}%"
        statement = statement.where(or_(Patient.name.ilike(keyword), Patient.case_number.ilike(keyword)))
    rows = [build_queue_item(db, visit, patient, clinic_session, prescription) for visit, patient, clinic_session, prescription in db.execute(statement)]
    if status_filter:
        rows = [
            row
            for row in rows
            if row.visit_status.value == status_filter
            or row.prescription_status == status_filter
            or (row.dispensing_status and row.dispensing_status.value == status_filter)
        ]
    return rows


def get_pharmacy_visit_detail(db: Session, visit_id: UUID) -> PharmacyVisitDetail:
    visit, patient, clinic_session, prescription = get_visit_context(db, visit_id)
    record = latest_record_for_prescription(db, prescription.id)
    return PharmacyVisitDetail(
        queue_item=build_queue_item(db, visit, patient, clinic_session, prescription),
        prescription=get_prescription(db, prescription.id),
        dispensing=get_dispensing_record(db, record.id) if record else None,
    )


def start_dispensing(db: Session, visit_id: UUID, actor: User) -> PharmacyVisitDetail:
    visit, _, _, prescription = get_visit_context(db, visit_id)
    prescription = get_prescription(db, prescription.id)
    if visit.status != VisitStatus.WAITING_FOR_PHARMACY:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Visit is not waiting for pharmacy")
    if prescription.status != PrescriptionStatus.SENT_TO_PHARMACY:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Prescription is not ready for dispensing")
    if not prescription.items:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Prescription has no items")
    if active_record_for_prescription(db, prescription.id) is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="This prescription is already being dispensed")
    now = datetime.now(timezone.utc)
    record = DispensingRecord(
        visit_id=visit.id,
        prescription_id=prescription.id,
        status=DispensingStatus.IN_PROGRESS,
        assigned_to=actor.id,
        started_at=now,
        created_by=actor.id,
        updated_by=actor.id,
    )
    db.add(record)
    db.flush()
    for prescription_item in prescription.items:
        db.add(
            DispensingItem(
                dispensing_record_id=record.id,
                prescription_item_id=prescription_item.id,
                medication_id=prescription_item.medication_id,
                prescribed_quantity=prescription_item.quantity,
                dispensed_quantity=Decimal("0.00"),
                unit=prescription_item.dose_unit,
            )
        )
    prescription.status = PrescriptionStatus.DISPENSING
    update_visit_status(db, visit, VisitStatus.DISPENSING, actor=actor, commit=False)
    write_audit_log(
        db,
        actor_user_id=actor.id,
        action="DISPENSING_STARTED",
        entity_type="dispensing_record",
        entity_id=record.id,
        summary=f"Started dispensing for visit {visit.id}",
    )
    db.commit()
    return get_pharmacy_visit_detail(db, visit_id)


def update_dispensing_items(
    db: Session,
    dispensing_id: UUID,
    payload: DispensingItemsUpdate,
    actor: User,
) -> DispensingRecord:
    record = get_dispensing_record(db, dispensing_id)
    if record.status != DispensingStatus.IN_PROGRESS:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Dispensing items can only be updated in progress")
    item_map = {item.id: item for item in record.items}
    for item_update in payload.items:
        item = item_map.get(item_update.id)
        if item is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dispensing item not found")
        if item_update.dispensed_quantity > item.prescribed_quantity:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Dispensed quantity cannot exceed prescribed quantity")
        item.dispensed_quantity = item_update.dispensed_quantity
        item.notes = item_update.notes
    record.notes = payload.notes
    record.version += 1
    record.updated_by = actor.id
    write_audit_log(
        db,
        actor_user_id=actor.id,
        action="DISPENSING_ITEMS_UPDATED",
        entity_type="dispensing_record",
        entity_id=record.id,
        summary=f"Updated dispensing items for record {record.id}",
    )
    db.commit()
    return get_dispensing_record(db, dispensing_id)


def ensure_dispensing_quantities(record: DispensingRecord) -> None:
    if not record.items:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Dispensing record has no items")
    for item in record.items:
        if item.dispensed_quantity <= 0:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Every item requires a dispensed quantity")
        if item.dispensed_quantity > item.prescribed_quantity:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Dispensed quantity cannot exceed prescribed quantity")


def submit_for_verification(db: Session, dispensing_id: UUID, actor: User) -> DispensingRecord:
    record = get_dispensing_record(db, dispensing_id)
    if record.status != DispensingStatus.IN_PROGRESS:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Dispensing is not in progress")
    ensure_dispensing_quantities(record)
    visit = db.get(Visit, record.visit_id)
    prescription = db.get(Prescription, record.prescription_id)
    if visit is None or prescription is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dispensing context not found")
    now = datetime.now(timezone.utc)
    record.status = DispensingStatus.WAITING_FOR_VERIFICATION
    record.prepared_by = actor.id
    record.prepared_at = now
    record.updated_by = actor.id
    record.version += 1
    prescription.status = PrescriptionStatus.WAITING_FOR_VERIFICATION
    update_visit_status(db, visit, VisitStatus.WAITING_FOR_VERIFICATION, actor=actor, commit=False)
    write_audit_log(
        db,
        actor_user_id=actor.id,
        action="SUBMITTED_FOR_VERIFICATION",
        entity_type="dispensing_record",
        entity_id=record.id,
        summary=f"Submitted dispensing record {record.id} for verification",
    )
    db.commit()
    return get_dispensing_record(db, dispensing_id)


def verify_dispensing(db: Session, dispensing_id: UUID, payload: DispensingVerify, actor: User) -> DispensingRecord:
    record = get_dispensing_record(db, dispensing_id)
    if record.status != DispensingStatus.WAITING_FOR_VERIFICATION:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Dispensing is not waiting for verification")
    if record.prepared_by == actor.id:
        if not is_admin(actor) or not payload.allow_self_verification or not payload.exception_reason.strip():
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Self verification requires admin exception")
        record.verification_exception = True
        record.verification_exception_reason = payload.exception_reason.strip()
        write_audit_log(
            db,
            actor_user_id=actor.id,
            action="SELF_VERIFICATION_EXCEPTION",
            entity_type="dispensing_record",
            entity_id=record.id,
            summary=payload.exception_reason.strip(),
        )
    visit = db.get(Visit, record.visit_id)
    prescription = db.get(Prescription, record.prescription_id)
    if visit is None or prescription is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dispensing context not found")
    now = datetime.now(timezone.utc)
    record.status = DispensingStatus.WAITING_FOR_PICKUP
    record.verified_by = actor.id
    record.verified_at = now
    record.updated_by = actor.id
    record.version += 1
    prescription.status = PrescriptionStatus.WAITING_FOR_PICKUP
    update_visit_status(db, visit, VisitStatus.WAITING_FOR_PICKUP, actor=actor, commit=False)
    write_audit_log(
        db,
        actor_user_id=actor.id,
        action="PRESCRIPTION_VERIFIED",
        entity_type="dispensing_record",
        entity_id=record.id,
        summary=f"Verified dispensing record {record.id}",
    )
    db.commit()
    return get_dispensing_record(db, dispensing_id)


def hand_out_medication(db: Session, dispensing_id: UUID, payload: DispensingHandOut, actor: User) -> DispensingRecord:
    existing = db.execute(
        select(DispensingRecord).where(DispensingRecord.handout_idempotency_key == payload.idempotency_key)
    ).scalar_one_or_none()
    if existing is not None and existing.id != dispensing_id:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Idempotency key was already used")
    record = get_dispensing_record(db, dispensing_id)
    if record.status == DispensingStatus.DISPENSED:
        if record.handout_idempotency_key == payload.idempotency_key:
            return record
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Medication was already handed out")
    if record.status != DispensingStatus.WAITING_FOR_PICKUP:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Dispensing is not waiting for pickup")
    ensure_dispensing_quantities(record)
    visit = db.get(Visit, record.visit_id)
    prescription = db.get(Prescription, record.prescription_id)
    if visit is None or prescription is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dispensing context not found")
    now = datetime.now(timezone.utc)
    record.status = DispensingStatus.DISPENSED
    record.handed_out_by = actor.id
    record.handed_out_at = now
    record.patient_counseling = payload.patient_counseling
    record.notes = payload.notes
    record.updated_by = actor.id
    record.version += 1
    record.handout_idempotency_key = payload.idempotency_key
    prescription.status = PrescriptionStatus.DISPENSED
    update_visit_status(db, visit, VisitStatus.COMPLETED, actor=actor, commit=False)
    write_audit_log(
        db,
        actor_user_id=actor.id,
        action="MEDICATION_HANDED_OUT",
        entity_type="dispensing_record",
        entity_id=record.id,
        summary=f"Handed out medication for visit {visit.id}",
    )
    db.commit()
    return get_dispensing_record(db, dispensing_id)


def return_to_clinic(db: Session, dispensing_id: UUID, payload: DispensingReturn, actor: User) -> DispensingRecord:
    record = get_dispensing_record(db, dispensing_id)
    if record.status not in {
        DispensingStatus.IN_PROGRESS,
        DispensingStatus.WAITING_FOR_VERIFICATION,
        DispensingStatus.VERIFIED,
        DispensingStatus.WAITING_FOR_PICKUP,
    }:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Dispensing cannot be returned in this status")
    visit = db.get(Visit, record.visit_id)
    prescription = db.get(Prescription, record.prescription_id)
    if visit is None or prescription is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dispensing context not found")
    record.status = DispensingStatus.RETURNED
    record.return_reason = payload.reason
    record.return_details = payload.details
    record.returned_by = actor.id
    record.returned_at = datetime.now(timezone.utc)
    record.updated_by = actor.id
    record.version += 1
    prescription.status = PrescriptionStatus.RETURNED_TO_CLINIC
    prescription.returned_reason = f"{payload.reason.value}: {payload.details}"
    prescription.returned_at = record.returned_at
    update_visit_status(db, visit, VisitStatus.IN_CONSULTATION, actor=actor, commit=False)
    write_audit_log(
        db,
        actor_user_id=actor.id,
        action="RETURNED_TO_CLINIC",
        entity_type="dispensing_record",
        entity_id=record.id,
        summary=f"{payload.reason.value}: {payload.details}",
    )
    db.commit()
    return get_dispensing_record(db, dispensing_id)
