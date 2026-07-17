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


def create_medication(client: TestClient, auth_headers: dict[str, str], code: str) -> str:
    response = client.post(
        "/api/v1/medications",
        headers=auth_headers,
        json={
            "code": code,
            "name": f"藥品 {code}",
            "generic_name": "",
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
    assert response.status_code == 201
    return response.json()["id"]


def create_batch(
    client: TestClient,
    auth_headers: dict[str, str],
    medication_id: str,
    batch_number: str,
    expiry_date: str,
    quantity: str,
) -> str:
    response = client.post(
        "/api/v1/inventory/batches",
        headers=auth_headers,
        json={
            "medication_id": medication_id,
            "batch_number": batch_number,
            "expiry_date": expiry_date,
            "quantity": quantity,
            "unit": "包",
            "location": "藥櫃 A",
        },
    )
    assert response.status_code == 201
    return response.json()["id"]


def create_visit_with_sent_prescription(
    client: TestClient,
    auth_headers: dict[str, str],
    medication_id: str,
    quantity: str,
    case_number: str,
) -> str:
    session_response = client.post(
        "/api/v1/clinic-sessions",
        headers=auth_headers,
        json={
            "name": f"Inventory clinic {case_number}",
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
            "name": "Inventory Patient",
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
    visit_id = visit_response.json()["id"]
    assert client.patch(f"/api/v1/visits/{visit_id}/status", headers=auth_headers, json={"status": "WAITING_FOR_CLINIC"}).status_code == 200
    assert client.post(f"/api/v1/clinic/queue/{visit_id}/start", headers=auth_headers).status_code == 200
    prescription = client.get(f"/api/v1/visits/{visit_id}/prescription", headers=auth_headers).json()
    assert client.post(
        f"/api/v1/prescriptions/{prescription['id']}/items",
        headers=auth_headers,
        json={
            "medication_id": medication_id,
            "dose": "1",
            "dose_unit": "包",
            "frequency": "每日三次",
            "route": "口服",
            "duration_days": 5,
            "quantity": quantity,
            "instructions": "飯後服用",
            "notes": "",
        },
    ).status_code == 201
    assert client.post(f"/api/v1/prescriptions/{prescription['id']}/confirm", headers=auth_headers).status_code == 200
    assert client.post(f"/api/v1/prescriptions/{prescription['id']}/send-to-pharmacy", headers=auth_headers).status_code == 200
    return visit_id


def test_inventory_batch_adjustment_and_transactions(client: TestClient, auth_headers: dict[str, str]):
    medication_id = create_medication(client, auth_headers, "INV-001")
    batch_id = create_batch(client, auth_headers, medication_id, "A1", "2027-01-01", "20.00")

    adjustment = client.post(
        "/api/v1/inventory/adjustments",
        headers=auth_headers,
        json={"batch_id": batch_id, "adjustment_type": "ADJUST_DECREASE", "quantity": "5.00", "reason": "盤點校正"},
    )

    assert adjustment.status_code == 200
    assert adjustment.json()["quantity_on_hand"] == "15.00"
    transactions = client.get("/api/v1/inventory/transactions", headers=auth_headers)
    assert transactions.status_code == 200
    assert [item["transaction_type"] for item in transactions.json()] == ["ADJUST_DECREASE", "RECEIVE"]


def test_fefo_reserves_multiple_batches_and_handout_deducts_stock(client: TestClient, auth_headers: dict[str, str]):
    medication_id = create_medication(client, auth_headers, "INV-002")
    first_batch = create_batch(client, auth_headers, medication_id, "EARLY", "2027-01-01", "10.00")
    second_batch = create_batch(client, auth_headers, medication_id, "LATE", "2027-06-01", "20.00")
    visit_id = create_visit_with_sent_prescription(client, auth_headers, medication_id, "15.00", "INV-FEFO")

    detail = client.post(f"/api/v1/pharmacy/queue/{visit_id}/start", headers=auth_headers)

    assert detail.status_code == 200
    dispensing = detail.json()["dispensing"]
    assert len(dispensing["items"]) == 2
    assert [item["inventory_batch"]["batch_number"] for item in dispensing["items"]] == ["EARLY", "LATE"]
    assert [item["prescribed_quantity"] for item in dispensing["items"]] == ["10.00", "5.00"]
    early = client.get(f"/api/v1/inventory/batches/{first_batch}", headers=auth_headers).json()
    late = client.get(f"/api/v1/inventory/batches/{second_batch}", headers=auth_headers).json()
    assert early["reserved_quantity"] == "10.00"
    assert late["reserved_quantity"] == "5.00"

    assert client.post(f"/api/v1/dispensing/{dispensing['id']}/submit-for-verification", headers=auth_headers).status_code == 200
    assert client.post(
        f"/api/v1/dispensing/{dispensing['id']}/verify",
        headers=auth_headers,
        json={"allow_self_verification": True, "exception_reason": "single pharmacist test"},
    ).status_code == 200
    assert client.post(
        f"/api/v1/dispensing/{dispensing['id']}/hand-out",
        headers=auth_headers,
        json={
            "patient_counseling": "已完成衛教。",
            "notes": "",
            "idempotency_key": "inventory-handout-001",
        },
    ).status_code == 200
    early_after = client.get(f"/api/v1/inventory/batches/{first_batch}", headers=auth_headers).json()
    late_after = client.get(f"/api/v1/inventory/batches/{second_batch}", headers=auth_headers).json()
    assert early_after["quantity_on_hand"] == "0.00"
    assert early_after["reserved_quantity"] == "0.00"
    assert late_after["quantity_on_hand"] == "15.00"
    assert late_after["reserved_quantity"] == "0.00"


def test_return_to_clinic_releases_reserved_inventory(client: TestClient, auth_headers: dict[str, str]):
    medication_id = create_medication(client, auth_headers, "INV-003")
    batch_id = create_batch(client, auth_headers, medication_id, "RETURN", "2027-01-01", "20.00")
    visit_id = create_visit_with_sent_prescription(client, auth_headers, medication_id, "8.00", "INV-RETURN")
    dispensing = client.post(f"/api/v1/pharmacy/queue/{visit_id}/start", headers=auth_headers).json()["dispensing"]
    reserved = client.get(f"/api/v1/inventory/batches/{batch_id}", headers=auth_headers).json()
    assert reserved["reserved_quantity"] == "8.00"

    returned = client.post(
        f"/api/v1/dispensing/{dispensing['id']}/return-to-clinic",
        headers=auth_headers,
        json={"reason": "UNCLEAR_DOSAGE", "details": "請確認劑量。"},
    )

    assert returned.status_code == 200
    released = client.get(f"/api/v1/inventory/batches/{batch_id}", headers=auth_headers).json()
    assert released["quantity_on_hand"] == "20.00"
    assert released["reserved_quantity"] == "0.00"


def test_insufficient_inventory_blocks_dispensing_start(client: TestClient, auth_headers: dict[str, str]):
    medication_id = create_medication(client, auth_headers, "INV-004")
    create_batch(client, auth_headers, medication_id, "LOW", "2027-01-01", "5.00")
    visit_id = create_visit_with_sent_prescription(client, auth_headers, medication_id, "10.00", "INV-LOW")

    response = client.post(f"/api/v1/pharmacy/queue/{visit_id}/start", headers=auth_headers)

    assert response.status_code == 409
