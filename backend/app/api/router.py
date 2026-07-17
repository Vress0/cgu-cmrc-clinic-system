from fastapi import APIRouter

from app.api.v1.health import router as health_router
from app.modules.auth.router import router as auth_router
from app.modules.audit_logs.router import router as audit_logs_router
from app.modules.clinic.router import router as clinic_router
from app.modules.clinic_sessions.router import router as clinic_sessions_router
from app.modules.consultations.router import router as consultations_router
from app.modules.consents.router import router as consents_router
from app.modules.dispensing.router import router as dispensing_router
from app.modules.health_histories.router import router as health_histories_router
from app.modules.medications.router import router as medications_router
from app.modules.patients.router import router as patients_router
from app.modules.prescriptions.router import router as prescriptions_router
from app.modules.vital_signs.router import router as vital_signs_router
from app.modules.visits.router import router as visits_router

api_router = APIRouter()
api_router.include_router(health_router, tags=["health"])
api_router.include_router(auth_router)
api_router.include_router(clinic_sessions_router)
api_router.include_router(patients_router)
api_router.include_router(health_histories_router)
api_router.include_router(consents_router)
api_router.include_router(visits_router)
api_router.include_router(medications_router)
api_router.include_router(clinic_router)
api_router.include_router(vital_signs_router)
api_router.include_router(consultations_router)
api_router.include_router(prescriptions_router)
api_router.include_router(dispensing_router)
api_router.include_router(audit_logs_router)
