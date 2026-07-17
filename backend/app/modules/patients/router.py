from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.modules.auth.dependencies import require_permissions
from app.modules.patients.models import Patient
from app.modules.patients.schemas import PatientCreate, PatientRead, PatientUpdate

router = APIRouter(prefix="/patients", tags=["patients"])


@router.get("", response_model=list[PatientRead])
def list_patients(
    q: str | None = Query(default=None, max_length=80),
    db: Session = Depends(get_db),
    _=Depends(require_permissions("patients:read")),
) -> list[Patient]:
    statement = select(Patient).order_by(Patient.created_at.desc())
    if q:
        pattern = f"%{q}%"
        statement = statement.where(or_(Patient.name.ilike(pattern), Patient.case_number.ilike(pattern)))
    return list(db.execute(statement.limit(50)).scalars())


@router.post("", response_model=PatientRead, status_code=201)
def create_patient(
    payload: PatientCreate,
    db: Session = Depends(get_db),
    _=Depends(require_permissions("patients:write")),
) -> Patient:
    patient = Patient(**payload.model_dump())
    db.add(patient)
    db.commit()
    db.refresh(patient)
    return patient


@router.get("/{patient_id}", response_model=PatientRead)
def get_patient(
    patient_id: UUID,
    db: Session = Depends(get_db),
    _=Depends(require_permissions("patients:read")),
) -> Patient:
    patient = db.get(Patient, patient_id)
    if patient is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="找不到個案")
    return patient


@router.patch("/{patient_id}", response_model=PatientRead)
def update_patient(
    patient_id: UUID,
    payload: PatientUpdate,
    db: Session = Depends(get_db),
    _=Depends(require_permissions("patients:write")),
) -> Patient:
    patient = db.get(Patient, patient_id)
    if patient is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="找不到個案")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(patient, key, value)
    db.add(patient)
    db.commit()
    db.refresh(patient)
    return patient
