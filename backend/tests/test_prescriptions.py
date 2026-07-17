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
            Permission(code="prescriptions:confirm", description="confirm prescriptions"),
            Permission(code="inventory:manage", description="inventory"),
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


def create_visit_in_consultation(client: TestClient, auth_headers: dict[str, str]) -> str:
    session_response = client.post(
        "/api/v1/clinic-sessions",
        headers=auth_headers,
        json={
            "name": "Prescription clinic",
            "session_date": "2026-07-17",
            "start_time": "09:00:00",
            "end_time": "12:00:00",
            "location": "Campus",
            "owner": "CMRC",
            "status": "ACTIVE",
        },
    )
    assert session_response.status_code == 201
    patient_response = client.post(
        "/api/v1/patients",
        headers=auth_headers,
        json={
            "case_number": "RX-1001",
            "name": "Prescription Patient",
            "sex": "FEMALE",
            "birth_date": "1950-01-01",
            "phone": "0900000000",
        },
    )
    assert patient_response.status_code == 201
    visit_response = client.post(
        "/api/v1/visits",
        headers=auth_headers,
        json={
            "clinic_session_id": session_response.json()["id"],
            "patient_id": patient_response.json()["id"],
            "registration_staff": "registration",
        },
    )
    assert visit_response.status_code == 201
    visit_id = visit_response.json()["id"]
    waiting_response = client.patch(
        f"/api/v1/visits/{visit_id}/status",
        headers=auth_headers,
        json={"status": "WAITING_FOR_CLINIC"},
    )
    assert waiting_response.status_code == 200
    start_response = client.post(f"/api/v1/clinic/queue/{visit_id}/start", headers=auth_headers)
    assert start_response.status_code == 200
    return visit_id


def create_medication(client: TestClient, auth_headers: dict[str, str], code: str = "M001") -> dict:
    response = client.post(
        "/api/v1/medications",
        headers=auth_headers,
        json={
            "code": code,
            "name": "葛根湯",
            "generic_name": "Ge Gen Tang",
            "brand_name": "",
            "dosage_form": "濃縮顆粒",
            "strength": "3g",
            "unit": "包",
            "route": "口服",
            "manufacturer": "示範藥廠",
            "notes": "",
            "warnings": "孕婦需評估",
            "is_active": True,
        },
    )
    assert response.status_code == 201
    return response.json()


def test_inactive_medication_cannot_be_added_to_prescription(client: TestClient, auth_headers: dict[str, str]):
    visit_id = create_visit_in_consultation(client, auth_headers)
    medication = create_medication(client, auth_headers)
    deactivate_response = client.post(f"/api/v1/medications/{medication['id']}/deactivate", headers=auth_headers)
    assert deactivate_response.status_code == 200
    prescription_response = client.get(f"/api/v1/visits/{visit_id}/prescription", headers=auth_headers)
    assert prescription_response.status_code == 200

    add_response = client.post(
        f"/api/v1/prescriptions/{prescription_response.json()['id']}/items",
        headers=auth_headers,
        json={
            "medication_id": medication["id"],
            "dose": "1",
            "dose_unit": "包",
            "frequency": "每日三次",
            "route": "口服",
            "duration_days": 3,
            "quantity": "9.00",
            "instructions": "飯後服用",
            "notes": "",
        },
    )

    assert add_response.status_code == 409


def test_confirmed_prescription_can_be_sent_to_pharmacy(client: TestClient, auth_headers: dict[str, str]):
    visit_id = create_visit_in_consultation(client, auth_headers)
    medication = create_medication(client, auth_headers)
    prescription = client.get(f"/api/v1/visits/{visit_id}/prescription", headers=auth_headers).json()

    add_response = client.post(
        f"/api/v1/prescriptions/{prescription['id']}/items",
        headers=auth_headers,
        json={
            "medication_id": medication["id"],
            "dose": "1",
            "dose_unit": "包",
            "frequency": "每日三次",
            "route": "口服",
            "duration_days": 3,
            "quantity": "9.00",
            "instructions": "飯後服用",
            "notes": "",
        },
    )
    assert add_response.status_code == 201
    confirm_response = client.post(f"/api/v1/prescriptions/{prescription['id']}/confirm", headers=auth_headers)
    assert confirm_response.status_code == 200
    assert confirm_response.json()["status"] == "CONFIRMED"

    send_response = client.post(f"/api/v1/prescriptions/{prescription['id']}/send-to-pharmacy", headers=auth_headers)
    assert send_response.status_code == 200
    assert send_response.json()["status"] == "SENT_TO_PHARMACY"

    visits_response = client.get("/api/v1/visits", headers=auth_headers)
    visit = [item for item in visits_response.json() if item["id"] == visit_id][0]
    assert visit["status"] == "WAITING_FOR_PHARMACY"

    edit_response = client.patch(
        f"/api/v1/prescription-items/{send_response.json()['items'][0]['id']}",
        headers=auth_headers,
        json={"frequency": "每日兩次"},
    )
    assert edit_response.status_code == 409


def test_cannot_send_empty_prescription(client: TestClient, auth_headers: dict[str, str]):
    visit_id = create_visit_in_consultation(client, auth_headers)
    prescription = client.get(f"/api/v1/visits/{visit_id}/prescription", headers=auth_headers).json()

    confirm_response = client.post(f"/api/v1/prescriptions/{prescription['id']}/confirm", headers=auth_headers)

    assert confirm_response.status_code == 409
