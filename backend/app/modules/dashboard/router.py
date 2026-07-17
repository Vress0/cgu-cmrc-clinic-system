from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.modules.auth.dependencies import get_current_user
from app.modules.clinic_sessions.models import ClinicSession, ClinicSessionStatus
from app.modules.dashboard.schemas import DashboardSummary
from app.modules.inventory.service import inventory_summary
from app.modules.medications.models import Medication
from app.modules.patients.models import Patient
from app.modules.visits.models import Visit, VisitStatus

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/summary", response_model=DashboardSummary)
def get_dashboard_summary(
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
) -> DashboardSummary:
    status_counts = {
        status_value: count
        for status_value, count in db.execute(select(Visit.status, func.count(Visit.id)).group_by(Visit.status)).all()
    }
    inventory = inventory_summary(db)
    return DashboardSummary(
        registered=status_counts.get(VisitStatus.REGISTERED, 0),
        waiting_for_clinic=status_counts.get(VisitStatus.WAITING_FOR_CLINIC, 0),
        in_consultation=status_counts.get(VisitStatus.IN_CONSULTATION, 0),
        waiting_for_pharmacy=status_counts.get(VisitStatus.WAITING_FOR_PHARMACY, 0),
        dispensing=status_counts.get(VisitStatus.DISPENSING, 0),
        waiting_for_verification=status_counts.get(VisitStatus.WAITING_FOR_VERIFICATION, 0),
        waiting_for_pickup=status_counts.get(VisitStatus.WAITING_FOR_PICKUP, 0),
        completed=status_counts.get(VisitStatus.COMPLETED, 0),
        cancelled=status_counts.get(VisitStatus.CANCELLED, 0),
        active_sessions=db.execute(
            select(func.count(ClinicSession.id)).where(ClinicSession.status == ClinicSessionStatus.ACTIVE)
        ).scalar_one(),
        patient_count=db.execute(select(func.count(Patient.id))).scalar_one(),
        medication_count=db.execute(select(func.count(Medication.id))).scalar_one(),
        inventory_available=inventory.total_available,
        low_stock_count=inventory.low_stock_count,
        expiring_count=inventory.expiring_count,
        expired_count=inventory.expired_count,
    )
