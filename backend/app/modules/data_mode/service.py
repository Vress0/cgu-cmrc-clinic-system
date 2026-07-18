from datetime import date, datetime, time, timezone
from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.data_mode import DATA_MODE_LABELS, DataMode
from app.modules.audit_logs.models import AuditLog
from app.modules.audit_logs.service import write_audit_log
from app.modules.clinic_sessions.models import ClinicSession, ClinicSessionStatus
from app.modules.consents.models import Consent
from app.modules.consultations.models import Consultation
from app.modules.data_mode.schemas import DemoDataStatus
from app.modules.dispensing.models import DispensingItem, DispensingRecord
from app.modules.health_histories.models import HealthHistory
from app.modules.inventory.models import InventoryBatch, InventoryTransaction, InventoryTransactionType
from app.modules.medications.models import Medication
from app.modules.patients.models import Patient
from app.modules.prescriptions.models import Prescription, PrescriptionItem, PrescriptionStatus
from app.modules.queue.models import QueueRecord
from app.modules.users.models import User
from app.modules.visits.models import Visit, VisitStatus
from app.modules.vital_signs.models import VitalSign

DEMO_DELETE_CONFIRMATION = "DELETE DEMO DATA"


def can_switch_data_mode(user: User) -> bool:
    return any(role.name == "admin" for role in user.roles) or any(
        permission.code == "data_mode.switch" for role in user.roles for permission in role.permissions
    )


def ensure_demo_enabled() -> None:
    if not settings.ENABLE_DEMO_MODE:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Demo mode is disabled")


def ensure_demo_manager(user: User) -> None:
    granted = {permission.code for role in user.roles for permission in role.permissions}
    if "demo_data.manage" not in granted and not any(role.name == "admin" for role in user.roles):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Demo data management permission required")


def data_mode_label(mode: DataMode) -> str:
    return DATA_MODE_LABELS[mode]


def switch_user_mode(db: Session, user: User, mode: DataMode, confirmation: str) -> str:
    ensure_demo_enabled() if mode == DataMode.DEMO else None
    if not can_switch_data_mode(user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Data mode switch permission required")
    if mode == DataMode.LIVE and confirmation != "SWITCH TO LIVE":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Confirmation must be SWITCH TO LIVE")
    if mode == DataMode.DEMO and confirmation != "SWITCH TO DEMO":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Confirmation must be SWITCH TO DEMO")
    if mode == DataMode.LIVE and not user.can_access_live:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No live data access")
    if mode == DataMode.DEMO and not user.can_access_demo:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No demo data access")

    previous_mode = user.current_data_mode
    user.current_data_mode = mode
    db.info["data_mode"] = mode
    write_audit_log(
        db,
        actor_user_id=user.id,
        action="DATA_MODE_SWITCHED",
        entity_type="data_mode",
        entity_id=None,
        summary=f"Switched data mode from {previous_mode.value} to {mode.value}",
    )
    db.commit()
    return f"Switched to {data_mode_label(mode)} mode."


def with_demo_scope(db: Session) -> None:
    db.info["data_mode"] = DataMode.DEMO


def demo_status(db: Session) -> DemoDataStatus:
    with_demo_scope(db)
    return DemoDataStatus(
        enabled=settings.ENABLE_DEMO_MODE,
        patient_count=db.execute(select(func.count(Patient.id))).scalar_one(),
        session_count=db.execute(select(func.count(ClinicSession.id))).scalar_one(),
        visit_count=db.execute(select(func.count(Visit.id))).scalar_one(),
        prescription_count=db.execute(select(func.count(Prescription.id))).scalar_one(),
        inventory_batch_count=db.execute(select(func.count(InventoryBatch.id))).scalar_one(),
        audit_log_count=db.execute(select(func.count(AuditLog.id))).scalar_one(),
    )


def delete_demo_data(db: Session, actor: User, *, confirmation: str) -> DemoDataStatus:
    ensure_demo_enabled()
    ensure_demo_manager(actor)
    if confirmation != DEMO_DELETE_CONFIRMATION:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Confirmation must be {DEMO_DELETE_CONFIRMATION}")
    previous_mode = db.info.get("data_mode", DataMode.LIVE)
    db.info["skip_data_mode_filter"] = True
    try:
        for model in [
            InventoryTransaction,
            DispensingItem,
            DispensingRecord,
            PrescriptionItem,
            Prescription,
            Consultation,
            VitalSign,
            QueueRecord,
            Visit,
            Consent,
            HealthHistory,
            InventoryBatch,
            Patient,
            ClinicSession,
            AuditLog,
        ]:
            db.execute(delete(model).where(model.data_mode == DataMode.DEMO))
        db.info["skip_data_mode_filter"] = False
        db.info["data_mode"] = DataMode.DEMO
        write_audit_log(
            db,
            actor_user_id=actor.id,
            action="DEMO_DATA_DELETED",
            entity_type="demo_data",
            entity_id=None,
            summary="Deleted all demo data",
        )
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.info.pop("skip_data_mode_filter", None)
        db.info["data_mode"] = previous_mode
    return demo_status(db)


def get_or_create_demo_medication(db: Session, code: str, name: str, unit: str) -> Medication:
    medication = db.execute(select(Medication).where(Medication.code == code)).scalar_one_or_none()
    if medication is not None:
        return medication
    medication = Medication(
        code=code,
        name=name,
        generic_name=name,
        dosage_form="granule",
        strength="demo",
        unit=unit,
        route="PO",
        manufacturer="DEMO",
        notes="Demo shared medication master",
        warnings="",
        is_active=True,
    )
    db.add(medication)
    db.flush()
    return medication


def seed_demo_data(db: Session, actor: User) -> DemoDataStatus:
    ensure_demo_enabled()
    ensure_demo_manager(actor)
    db.info["data_mode"] = DataMode.DEMO
    if db.execute(select(func.count(Patient.id))).scalar_one() > 0:
        write_audit_log(
            db,
            actor_user_id=actor.id,
            action="DEMO_DATA_SEEDED",
            entity_type="demo_data",
            entity_id=None,
            summary="Demo data already existed; seed skipped",
        )
        db.commit()
        return demo_status(db)

    today = date.today()
    morning = ClinicSession(
        name="DEMO Morning Clinic",
        session_date=today,
        start_time=time(9, 0),
        end_time=time(12, 0),
        location="Demo community center",
        owner="Demo registration team",
        notes="Demo session",
        status=ClinicSessionStatus.ACTIVE,
    )
    afternoon = ClinicSession(
        name="DEMO Afternoon Clinic",
        session_date=today,
        start_time=time(13, 30),
        end_time=time(16, 30),
        location="Demo community center",
        owner="Demo registration team",
        notes="Demo session",
        status=ClinicSessionStatus.ACTIVE,
    )
    db.add_all([morning, afternoon])
    db.flush()

    medications = [
        get_or_create_demo_medication(db, "DEMO-G001", "Demo Gan-Mai-Da-Zao", "pack"),
        get_or_create_demo_medication(db, "DEMO-G002", "Demo Yin-Qiao-San", "pack"),
        get_or_create_demo_medication(db, "DEMO-G003", "Demo Suan-Zao-Ren-Tang", "pack"),
    ]
    now = datetime.now(timezone.utc)
    for index, medication in enumerate(medications, start=1):
        batch = InventoryBatch(
            medication_id=medication.id,
            batch_number=f"DEMO-BATCH-{index:02d}",
            expiry_date=date(today.year + 1, min(index + 1, 12), 1),
            quantity_on_hand=Decimal("120.00"),
            reserved_quantity=Decimal("0.00"),
            unit=medication.unit,
            location="Demo pharmacy cabinet",
            received_at=now,
            is_active=True,
            created_by=actor.id,
            updated_by=actor.id,
        )
        db.add(batch)
        db.flush()
        db.add(
            InventoryTransaction(
                medication_id=medication.id,
                inventory_batch_id=batch.id,
                transaction_type=InventoryTransactionType.RECEIVE,
                quantity=Decimal("120.00"),
                quantity_before=Decimal("0.00"),
                quantity_after=Decimal("120.00"),
                reserved_before=Decimal("0.00"),
                reserved_after=Decimal("0.00"),
                reference_type="demo_seed",
                reference_id=batch.id,
                reason="Seed demo inventory",
                performed_by=actor.id,
                created_at=now,
            )
        )

    statuses = [
        VisitStatus.WAITING_FOR_CLINIC,
        VisitStatus.IN_CONSULTATION,
        VisitStatus.WAITING_FOR_PHARMACY,
        VisitStatus.WAITING_FOR_VERIFICATION,
        VisitStatus.WAITING_FOR_PICKUP,
        VisitStatus.COMPLETED,
        VisitStatus.REGISTERED,
    ]
    for index in range(1, 21):
        patient = Patient(
            case_number=f"DEMO-{index:04d}",
            name=f"Demo Patient {index:02d}",
            sex="F" if index % 2 else "M",
            birth_date=date(1950 + (index % 35), (index % 12) + 1, (index % 27) + 1),
            phone=f"0900-000-{index:03d}",
            residence_area="Demo district",
            emergency_contact="Demo family",
            emergency_contact_phone="0900-999-999",
            primary_language="Mandarin",
            assistance_needs="Needs larger font guidance" if index % 5 == 0 else "",
        )
        db.add(patient)
        db.flush()
        db.add(
            HealthHistory(
                patient_id=patient.id,
                chronic_diseases="Hypertension" if index % 4 == 0 else "",
                allergies="Penicillin" if index % 6 == 0 else "",
                current_medications="Demo medication note",
                surgery_history="",
                fall_history="",
                smoking_status="none",
                alcohol_status="none",
                sleep_status="interrupted" if index % 3 == 0 else "normal",
                diet_status="regular",
                notes="Demo health history",
            )
        )
        db.add(
            Consent(
                patient_id=patient.id,
                version="demo-v1",
                method="written",
                consented_at=now,
                staff_name="Demo staff",
                consented_by=actor.id,
                service_consent=True,
                research_consent=index % 2 == 0,
                notes="Demo consent",
            )
        )
        session = morning if index <= 10 else afternoon
        visit_status = statuses[(index - 1) % len(statuses)]
        visit = Visit(
            clinic_session_id=session.id,
            patient_id=patient.id,
            queue_number=index if index <= 10 else index - 10,
            registered_at=now,
            status=visit_status,
            registration_staff="Demo staff",
            notes="Demo visit",
            completed_at=now if visit_status == VisitStatus.COMPLETED else None,
        )
        db.add(visit)
        db.flush()
        db.add(QueueRecord(clinic_session_id=session.id, visit_id=visit.id, queue_number=visit.queue_number))
        if visit_status in {VisitStatus.IN_CONSULTATION, VisitStatus.WAITING_FOR_PHARMACY, VisitStatus.COMPLETED}:
            db.add(
                Consultation(
                    visit_id=visit.id,
                    chief_complaint="Demo chief complaint",
                    symptom_description="Demo symptom description",
                    requires_pharmacy=visit_status != VisitStatus.IN_CONSULTATION,
                    clinician_notes="Demo clinical note",
                )
            )
        if visit_status in {
            VisitStatus.WAITING_FOR_PHARMACY,
            VisitStatus.WAITING_FOR_VERIFICATION,
            VisitStatus.WAITING_FOR_PICKUP,
            VisitStatus.COMPLETED,
        }:
            prescription = Prescription(
                visit_id=visit.id,
                status=PrescriptionStatus.SENT_TO_PHARMACY
                if visit_status == VisitStatus.WAITING_FOR_PHARMACY
                else PrescriptionStatus.WAITING_FOR_PICKUP,
                created_by=actor.id,
                confirmed_by=actor.id,
                confirmed_at=now,
                sent_to_pharmacy_at=now,
            )
            db.add(prescription)
            db.flush()
            db.add(
                PrescriptionItem(
                    prescription_id=prescription.id,
                    medication_id=medications[index % len(medications)].id,
                    dose="1",
                    dose_unit="pack",
                    frequency="BID",
                    route="PO",
                    duration_days=3,
                    quantity=Decimal("6.00"),
                    instructions="Demo instructions",
                    notes="Demo prescription item",
                )
            )

    write_audit_log(
        db,
        actor_user_id=actor.id,
        action="DEMO_DATA_SEEDED",
        entity_type="demo_data",
        entity_id=None,
        summary="Seeded demo sessions, patients, visits, prescriptions and inventory",
    )
    db.commit()
    return demo_status(db)


def reset_demo_data(db: Session, actor: User) -> DemoDataStatus:
    if not settings.ALLOW_DEMO_RESET:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Demo reset is disabled")
    delete_demo_data(db, actor, confirmation=DEMO_DELETE_CONFIRMATION)
    return seed_demo_data(db, actor)
