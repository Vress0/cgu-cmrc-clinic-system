from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.modules.auth.dependencies import require_permissions
from app.modules.consultations.models import Consultation
from app.modules.consultations.schemas import (
    ConsultationClinicalUpdate,
    ConsultationComplete,
    ConsultationIntakeUpdate,
    ConsultationRead,
)
from app.modules.consultations.service import (
    complete_consultation,
    get_or_create_consultation,
    get_visit_or_404,
    update_clinical,
    update_intake,
)
from app.modules.users.models import User

router = APIRouter(tags=["consultations"])


@router.get("/visits/{visit_id}/consultation", response_model=ConsultationRead)
def get_consultation(
    visit_id: UUID,
    db: Session = Depends(get_db),
    _=Depends(require_permissions("clinic:write")),
) -> Consultation:
    visit = get_visit_or_404(db, visit_id)
    consultation = get_or_create_consultation(db, visit)
    db.commit()
    db.refresh(consultation)
    return consultation


@router.put("/visits/{visit_id}/consultation/intake", response_model=ConsultationRead)
def put_consultation_intake(
    visit_id: UUID,
    payload: ConsultationIntakeUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions("clinic:write")),
) -> Consultation:
    return update_intake(db, visit_id, payload, current_user)


@router.put("/visits/{visit_id}/consultation/clinical", response_model=ConsultationRead)
def put_consultation_clinical(
    visit_id: UUID,
    payload: ConsultationClinicalUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions("clinic:write")),
) -> Consultation:
    return update_clinical(db, visit_id, payload, current_user)


@router.post("/visits/{visit_id}/consultation/complete", response_model=ConsultationRead)
def post_consultation_complete(
    visit_id: UUID,
    payload: ConsultationComplete,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions("clinic:write")),
) -> Consultation:
    return complete_consultation(db, visit_id, payload, current_user)
