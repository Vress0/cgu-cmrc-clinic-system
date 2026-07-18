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
            Permission(code="patients:read", description="read patients"),
            Permission(code="patients:write", description="write patients"),
            Permission(code="visits:manage", description="visits"),
            Permission(code="inventory:manage", description="inventory"),
            Permission(code="audit_logs:read", description="audit logs"),
            Permission(code="data_mode.live.access", description="live"),
            Permission(code="data_mode.demo.access", description="demo"),
            Permission(code="data_mode.switch", description="switch"),
            Permission(code="demo_data.manage", description="demo manage"),
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


def create_patient(client: TestClient, auth_headers: dict[str, str], case_number: str, name: str) -> str:
    response = client.post(
        "/api/v1/patients",
        headers=auth_headers,
        json={
            "case_number": case_number,
            "name": name,
            "sex": "F",
            "birth_date": "1950-01-01",
        },
    )
    assert response.status_code == 201
    return response.json()["id"]


def create_clinic_session(client: TestClient, auth_headers: dict[str, str], name: str) -> str:
    response = client.post(
        "/api/v1/clinic-sessions",
        headers=auth_headers,
        json={
            "name": name,
            "session_date": "2026-07-18",
            "start_time": "09:00:00",
            "end_time": "12:00:00",
            "location": "Demo hall",
            "owner": "CMRC",
            "status": "ACTIVE",
        },
    )
    assert response.status_code == 201
    return response.json()["id"]


def create_visit(client: TestClient, auth_headers: dict[str, str], session_id: str, patient_id: str) -> str:
    response = client.post(
        "/api/v1/visits",
        headers=auth_headers,
        json={
            "clinic_session_id": session_id,
            "patient_id": patient_id,
            "registration_staff": "Registration",
        },
    )
    assert response.status_code == 201
    return response.json()["id"]


def create_medication(client: TestClient, auth_headers: dict[str, str], code: str) -> str:
    response = client.post(
        "/api/v1/medications",
        headers=auth_headers,
        json={
            "code": code,
            "name": f"Medication {code}",
            "generic_name": "",
            "brand_name": "",
            "dosage_form": "granule",
            "strength": "3g",
            "unit": "pack",
            "route": "PO",
            "manufacturer": "Demo maker",
            "notes": "",
            "warnings": "",
            "is_active": True,
        },
    )
    assert response.status_code == 201
    return response.json()["id"]


def create_inventory_batch(client: TestClient, auth_headers: dict[str, str], medication_id: str, batch_number: str) -> str:
    response = client.post(
        "/api/v1/inventory/batches",
        headers=auth_headers,
        json={
            "medication_id": medication_id,
            "batch_number": batch_number,
            "expiry_date": "2027-07-18",
            "quantity": "12.00",
            "unit": "pack",
            "location": "Cabinet A",
        },
    )
    assert response.status_code == 201
    return response.json()["id"]


def switch_mode(client: TestClient, auth_headers: dict[str, str], mode: str) -> None:
    response = client.post(
        "/api/v1/data-mode/switch",
        headers=auth_headers,
        json={"mode": mode, "confirmation": f"SWITCH TO {mode}"},
    )
    assert response.status_code == 200
    assert response.json()["mode"] == mode


def test_live_and_demo_patient_queries_are_isolated(client: TestClient, auth_headers: dict[str, str]):
    live_id = create_patient(client, auth_headers, "DM-0001", "Live Patient")
    live_list = client.get("/api/v1/patients", headers=auth_headers)
    assert live_list.status_code == 200
    assert [patient["name"] for patient in live_list.json()] == ["Live Patient"]

    switch_mode(client, auth_headers, "DEMO")
    demo_empty = client.get("/api/v1/patients", headers=auth_headers)
    assert demo_empty.status_code == 200
    assert demo_empty.json() == []

    demo_id = create_patient(client, auth_headers, "DM-0001", "Demo Patient")
    assert demo_id != live_id
    demo_list = client.get("/api/v1/patients", headers=auth_headers)
    assert [patient["name"] for patient in demo_list.json()] == ["Demo Patient"]

    live_cross_read = client.get(f"/api/v1/patients/{live_id}", headers=auth_headers)
    assert live_cross_read.status_code == 404

    switch_mode(client, auth_headers, "LIVE")
    live_list_again = client.get("/api/v1/patients", headers=auth_headers)
    assert [patient["name"] for patient in live_list_again.json()] == ["Live Patient"]
    demo_cross_read = client.get(f"/api/v1/patients/{demo_id}", headers=auth_headers)
    assert demo_cross_read.status_code == 404


def test_delete_demo_data_does_not_delete_live_records(client: TestClient, auth_headers: dict[str, str]):
    create_patient(client, auth_headers, "LIVE-KEEP", "Keep Live")
    switch_mode(client, auth_headers, "DEMO")
    create_patient(client, auth_headers, "DEMO-DELETE", "Delete Demo")

    delete_response = client.request(
        "DELETE",
        "/api/v1/demo-data",
        headers=auth_headers,
        json={"confirmation": "DELETE DEMO DATA"},
    )
    assert delete_response.status_code == 200
    assert delete_response.json()["patient_count"] == 0

    switch_mode(client, auth_headers, "LIVE")
    live_list = client.get("/api/v1/patients", headers=auth_headers)
    assert [patient["case_number"] for patient in live_list.json()] == ["LIVE-KEEP"]


def test_seed_demo_data_is_idempotent_and_contains_demo_scenarios(client: TestClient, auth_headers: dict[str, str]):
    first_seed = client.post("/api/v1/demo-data/seed", headers=auth_headers)
    second_seed = client.post("/api/v1/demo-data/seed", headers=auth_headers)

    assert first_seed.status_code == 200
    assert second_seed.status_code == 200
    assert first_seed.json()["patient_count"] == 20
    assert first_seed.json()["session_count"] == 2
    assert first_seed.json()["inventory_batch_count"] >= 7
    assert second_seed.json()["patient_count"] == first_seed.json()["patient_count"]
    assert second_seed.json()["inventory_batch_count"] == first_seed.json()["inventory_batch_count"]

    switch_mode(client, auth_headers, "DEMO")
    patients = client.get("/api/v1/patients", headers=auth_headers)
    inventory_summary = client.get("/api/v1/inventory/summary", headers=auth_headers)
    assert patients.status_code == 200
    assert all(patient["name"].startswith("示範個案") for patient in patients.json())
    assert inventory_summary.status_code == 200
    assert inventory_summary.json()["low_stock_count"] >= 2
    assert inventory_summary.json()["expired_count"] >= 1


def test_visits_inventory_dashboard_and_audit_are_mode_scoped(client: TestClient, auth_headers: dict[str, str]):
    live_patient_id = create_patient(client, auth_headers, "LIVE-SCOPE", "Live Scoped")
    live_session_id = create_clinic_session(client, auth_headers, "Live Scoped Clinic")
    live_visit_id = create_visit(client, auth_headers, live_session_id, live_patient_id)
    medication_id = create_medication(client, auth_headers, "DM-SHARED-001")
    live_batch_id = create_inventory_batch(client, auth_headers, medication_id, "LIVE-BATCH")

    live_dashboard = client.get("/api/v1/dashboard/summary", headers=auth_headers)
    assert live_dashboard.status_code == 200
    assert live_dashboard.json()["patient_count"] == 1
    assert live_dashboard.json()["registered"] == 1
    assert live_dashboard.json()["inventory_available"] == "12.00"

    live_audits = client.get("/api/v1/audit-logs", headers=auth_headers)
    assert live_audits.status_code == 200
    assert {entry["data_mode"] for entry in live_audits.json()} == {"LIVE"}

    switch_mode(client, auth_headers, "DEMO")

    assert client.patch(f"/api/v1/visits/{live_visit_id}/status", headers=auth_headers, json={"status": "WAITING_FOR_CLINIC"}).status_code == 404
    assert client.get(f"/api/v1/inventory/batches/{live_batch_id}", headers=auth_headers).status_code == 404
    assert client.get("/api/v1/visits", headers=auth_headers).json() == []
    assert client.get("/api/v1/inventory", headers=auth_headers).json() == []

    demo_dashboard = client.get("/api/v1/dashboard/summary", headers=auth_headers)
    assert demo_dashboard.status_code == 200
    assert demo_dashboard.json()["patient_count"] == 0
    assert demo_dashboard.json()["registered"] == 0
    assert demo_dashboard.json()["inventory_available"] == "0.00"

    demo_patient_id = create_patient(client, auth_headers, "DEMO-SCOPE", "Demo Scoped")
    demo_session_id = create_clinic_session(client, auth_headers, "Demo Scoped Clinic")
    demo_visit_id = create_visit(client, auth_headers, demo_session_id, demo_patient_id)
    demo_batch_id = create_inventory_batch(client, auth_headers, medication_id, "DEMO-BATCH")

    demo_audits = client.get("/api/v1/audit-logs", headers=auth_headers)
    assert demo_audits.status_code == 200
    assert {entry["data_mode"] for entry in demo_audits.json()} == {"DEMO"}

    switch_mode(client, auth_headers, "LIVE")

    assert client.patch(f"/api/v1/visits/{demo_visit_id}/status", headers=auth_headers, json={"status": "WAITING_FOR_CLINIC"}).status_code == 404
    assert client.get(f"/api/v1/inventory/batches/{demo_batch_id}", headers=auth_headers).status_code == 404
    live_visits = client.get("/api/v1/visits", headers=auth_headers)
    assert live_visits.status_code == 200
    assert [visit["id"] for visit in live_visits.json()] == [live_visit_id]
    live_inventory = client.get("/api/v1/inventory", headers=auth_headers)
    assert live_inventory.status_code == 200
    assert [batch["id"] for batch in live_inventory.json()] == [live_batch_id]
