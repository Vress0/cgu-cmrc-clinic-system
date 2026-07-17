from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.security import hash_password
from app.db.base import Base
from app.db.session import get_db
from app.main import create_app
from app.modules.roles.models import Permission, Role
from app.modules.users.models import User


@pytest.fixture()
def db_session() -> Iterator[Session]:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    with session_factory() as session:
        permissions = [
            Permission(code="sessions:manage", description="sessions"),
            Permission(code="patients:read", description="patients read"),
            Permission(code="patients:write", description="patients write"),
            Permission(code="visits:manage", description="visits"),
            Permission(code="clinic:write", description="clinic"),
            Permission(code="audit_logs:read", description="audit logs"),
        ]
        role = Role(name="admin", description="admin", permissions=permissions)
        user = User(
            username="admin",
            email="admin@example.com",
            full_name="Admin",
            password_hash=hash_password("ChangeMe123!"),
            is_active=True,
            roles=[role],
        )
        session.add(user)
        session.commit()
        yield session


@pytest.fixture()
def client(db_session: Session) -> Iterator[TestClient]:
    app = create_app()

    def override_get_db() -> Iterator[Session]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture()
def auth_headers(client: TestClient) -> dict[str, str]:
    response = client.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": "ChangeMe123!"},
    )
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def create_session(client: TestClient, auth_headers: dict[str, str]) -> str:
    response = client.post(
        "/api/v1/clinic-sessions",
        headers=auth_headers,
        json={
            "name": "Clinic session",
            "session_date": "2026-07-17",
            "start_time": "09:00:00",
            "end_time": "12:00:00",
            "location": "Campus",
            "owner": "CMRC",
            "status": "ACTIVE",
        },
    )
    assert response.status_code == 201
    return response.json()["id"]


def create_patient(client: TestClient, auth_headers: dict[str, str]) -> str:
    response = client.post(
        "/api/v1/patients",
        headers=auth_headers,
        json={
            "case_number": "CGU-1001",
            "name": "Patient",
            "sex": "MALE",
            "birth_date": "1950-01-01",
            "phone": "0900000000",
        },
    )
    assert response.status_code == 201
    return response.json()["id"]


def create_visit(client: TestClient, auth_headers: dict[str, str]) -> str:
    session_id = create_session(client, auth_headers)
    patient_id = create_patient(client, auth_headers)
    response = client.post(
        "/api/v1/visits",
        headers=auth_headers,
        json={
            "clinic_session_id": session_id,
            "patient_id": patient_id,
            "registration_staff": "registration",
        },
    )
    assert response.status_code == 201
    visit_id = response.json()["id"]
    waiting_response = client.patch(
        f"/api/v1/visits/{visit_id}/status",
        headers=auth_headers,
        json={"status": "WAITING_FOR_CLINIC"},
    )
    assert waiting_response.status_code == 200
    return visit_id


def test_clinic_queue_start_vital_signs_and_complete_without_pharmacy(
    client: TestClient,
    auth_headers: dict[str, str],
):
    visit_id = create_visit(client, auth_headers)

    queue_response = client.get("/api/v1/clinic/queue", headers=auth_headers)
    assert queue_response.status_code == 200
    assert queue_response.json()[0]["visit_id"] == visit_id

    start_response = client.post(f"/api/v1/clinic/queue/{visit_id}/start", headers=auth_headers)
    assert start_response.status_code == 200
    assert start_response.json()["status"] == "IN_CONSULTATION"

    vital_response = client.post(
        f"/api/v1/visits/{visit_id}/vital-signs",
        headers=auth_headers,
        json={
            "systolic_blood_pressure": 120,
            "diastolic_blood_pressure": 80,
            "pulse": 72,
            "height_cm": "170",
            "weight_kg": "65",
            "blood_glucose_context": "fasting",
        },
    )
    assert vital_response.status_code == 201
    assert vital_response.json()["bmi"] == "22.49"

    intake_response = client.put(
        f"/api/v1/visits/{visit_id}/consultation/intake",
        headers=auth_headers,
        json={"chief_complaint": "headache", "symptom_description": "two days"},
    )
    assert intake_response.status_code == 200
    assert intake_response.json()["chief_complaint"] == "headache"

    clinical_response = client.put(
        f"/api/v1/visits/{visit_id}/consultation/clinical",
        headers=auth_headers,
        json={"assessment_summary": "stable", "requires_pharmacy": False},
    )
    assert clinical_response.status_code == 200

    complete_response = client.post(
        f"/api/v1/visits/{visit_id}/consultation/complete",
        headers=auth_headers,
        json={"requires_pharmacy": False},
    )
    assert complete_response.status_code == 200

    visit_response = client.get("/api/v1/visits", headers=auth_headers)
    completed = [visit for visit in visit_response.json() if visit["id"] == visit_id][0]
    assert completed["status"] == "COMPLETED"

    audit_response = client.get("/api/v1/audit-logs", headers=auth_headers)
    assert audit_response.status_code == 200
    assert len(audit_response.json()) >= 4


def test_invalid_clinic_transition_returns_conflict(client: TestClient, auth_headers: dict[str, str]):
    session_id = create_session(client, auth_headers)
    patient_id = create_patient(client, auth_headers)
    response = client.post(
        "/api/v1/visits",
        headers=auth_headers,
        json={
            "clinic_session_id": session_id,
            "patient_id": patient_id,
            "registration_staff": "registration",
        },
    )
    assert response.status_code == 201
    visit_id = response.json()["id"]

    start_response = client.post(f"/api/v1/clinic/queue/{visit_id}/start", headers=auth_headers)
    assert start_response.status_code == 409
