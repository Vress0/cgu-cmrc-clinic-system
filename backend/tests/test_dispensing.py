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
            Permission(code="pharmacy:dispense", description="pharmacy"),
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
    response = client.post("/api/v1/auth/login", json={"username": "admin", "password": "ChangeMe123!"})
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def create_visit_in_consultation(client: TestClient, auth_headers: dict[str, str], case_number: str) -> str:
    session_response = client.post(
        "/api/v1/clinic-sessions",
        headers=auth_headers,
        json={
            "name": f"Dispensing clinic {case_number}",
            "session_date": "2026-07-18",
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
            "case_number": case_number,
            "name": "Dispensing Patient",
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
    assert client.patch(f"/api/v1/visits/{visit_id}/status", headers=auth_headers, json={"status": "WAITING_FOR_CLINIC"}).status_code == 200
    assert client.post(f"/api/v1/clinic/queue/{visit_id}/start", headers=auth_headers).status_code == 200
    return visit_id


def create_sent_prescription(client: TestClient, auth_headers: dict[str, str], case_number: str = "DSP-1001") -> str:
    visit_id = create_visit_in_consultation(client, auth_headers, case_number)
    med_response = client.post(
        "/api/v1/medications",
        headers=auth_headers,
        json={
            "code": f"RX-{case_number}",
            "name": "葛根湯",
            "generic_name": "Ge Gen Tang",
            "brand_name": "",
            "dosage_form": "濃縮顆粒",
            "strength": "3g",
            "unit": "包",
            "route": "口服",
            "manufacturer": "示範藥廠",
            "notes": "",
            "warnings": "",
            "is_active": True,
        },
    )
    assert med_response.status_code == 201
    prescription = client.get(f"/api/v1/visits/{visit_id}/prescription", headers=auth_headers).json()
    add_response = client.post(
        f"/api/v1/prescriptions/{prescription['id']}/items",
        headers=auth_headers,
        json={
            "medication_id": med_response.json()["id"],
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
    assert client.post(f"/api/v1/prescriptions/{prescription['id']}/confirm", headers=auth_headers).status_code == 200
    assert client.post(f"/api/v1/prescriptions/{prescription['id']}/send-to-pharmacy", headers=auth_headers).status_code == 200
    return visit_id


def test_dispensing_full_flow_and_handout_idempotency(client: TestClient, auth_headers: dict[str, str]):
    visit_id = create_sent_prescription(client, auth_headers)

    queue_response = client.get("/api/v1/pharmacy/queue", headers=auth_headers)
    assert queue_response.status_code == 200
    assert queue_response.json()[0]["visit_id"] == visit_id

    start_response = client.post(f"/api/v1/pharmacy/queue/{visit_id}/start", headers=auth_headers)
    assert start_response.status_code == 200
    detail = start_response.json()
    dispensing_id = detail["dispensing"]["id"]
    dispensing_item = detail["dispensing"]["items"][0]
    assert detail["queue_item"]["visit_status"] == "DISPENSING"
    assert detail["prescription"]["status"] == "DISPENSING"

    duplicate_start = client.post(f"/api/v1/pharmacy/queue/{visit_id}/start", headers=auth_headers)
    assert duplicate_start.status_code == 409

    update_response = client.put(
        f"/api/v1/dispensing/{dispensing_id}/items",
        headers=auth_headers,
        json={"items": [{"id": dispensing_item["id"], "dispensed_quantity": "9.00", "notes": ""}], "notes": "prepared"},
    )
    assert update_response.status_code == 200
    submit_response = client.post(f"/api/v1/dispensing/{dispensing_id}/submit-for-verification", headers=auth_headers)
    assert submit_response.status_code == 200
    assert submit_response.json()["status"] == "WAITING_FOR_VERIFICATION"

    self_verify = client.post(
        f"/api/v1/dispensing/{dispensing_id}/verify",
        headers=auth_headers,
        json={"allow_self_verification": False, "exception_reason": ""},
    )
    assert self_verify.status_code == 409

    verify_response = client.post(
        f"/api/v1/dispensing/{dispensing_id}/verify",
        headers=auth_headers,
        json={"allow_self_verification": True, "exception_reason": "single pharmacist test"},
    )
    assert verify_response.status_code == 200
    assert verify_response.json()["status"] == "WAITING_FOR_PICKUP"

    handout_payload = {
        "patient_counseling": "已提醒飯後服用並注意身體反應。",
        "notes": "family picked up",
        "idempotency_key": "handout-key-001",
    }
    handout_response = client.post(f"/api/v1/dispensing/{dispensing_id}/hand-out", headers=auth_headers, json=handout_payload)
    assert handout_response.status_code == 200
    assert handout_response.json()["status"] == "DISPENSED"

    repeat_response = client.post(f"/api/v1/dispensing/{dispensing_id}/hand-out", headers=auth_headers, json=handout_payload)
    assert repeat_response.status_code == 200

    visits_response = client.get("/api/v1/visits", headers=auth_headers)
    completed = [visit for visit in visits_response.json() if visit["id"] == visit_id][0]
    assert completed["status"] == "COMPLETED"


def test_return_to_clinic_reopens_consultation(client: TestClient, auth_headers: dict[str, str]):
    visit_id = create_sent_prescription(client, auth_headers, "DSP-1002")
    detail = client.post(f"/api/v1/pharmacy/queue/{visit_id}/start", headers=auth_headers).json()
    dispensing_id = detail["dispensing"]["id"]

    return_response = client.post(
        f"/api/v1/dispensing/{dispensing_id}/return-to-clinic",
        headers=auth_headers,
        json={"reason": "UNCLEAR_DOSAGE", "details": "Dose frequency needs clarification."},
    )

    assert return_response.status_code == 200
    assert return_response.json()["status"] == "RETURNED"
    visit_detail = client.get(f"/api/v1/pharmacy/queue/{visit_id}", headers=auth_headers).json()
    assert visit_detail["prescription"]["status"] == "RETURNED_TO_CLINIC"
    assert visit_detail["queue_item"]["visit_status"] == "IN_CONSULTATION"
