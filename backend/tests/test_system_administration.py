from collections.abc import Iterator
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.security import hash_password
from app.db.base import Base
from app.db.session import get_db
from app.main import create_app
from app.modules.audit_logs.models import AuditLog
from app.modules.roles.models import Permission, Role
from app.modules.users.models import User


ALL_PERMISSIONS = [
    "users:manage",
    "roles:manage",
    "sessions:manage",
    "patients:read",
    "patients:write",
    "visits:manage",
    "clinic:write",
    "prescriptions:confirm",
    "pharmacy:dispense",
    "inventory:manage",
    "audit_logs:read",
    "exports:anonymous",
]


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
        permissions = [Permission(code=code, description=code) for code in ALL_PERMISSIONS]
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


def create_patient(client: TestClient, auth_headers: dict[str, str], case_number: str = "SYS-001") -> str:
    response = client.post(
        "/api/v1/patients",
        headers=auth_headers,
        json={
            "case_number": case_number,
            "name": "System Patient",
            "sex": "FEMALE",
            "birth_date": "1950-01-01",
            "phone": "0900000000",
            "primary_language": "Mandarin",
            "assistance_needs": "Walker assistance",
        },
    )
    assert response.status_code == 201
    return response.json()["id"]


def test_user_management_flow_writes_audit_logs(client: TestClient, auth_headers: dict[str, str]):
    roles = client.get("/api/v1/roles", headers=auth_headers)
    assert roles.status_code == 200
    assert "registration" in {role["name"] for role in roles.json()}

    created = client.post(
        "/api/v1/users",
        headers=auth_headers,
        json={
            "username": "reg01",
            "email": "reg01@example.com",
            "full_name": "Registration Staff",
            "password": "ChangeMe123!",
            "roles": ["registration"],
            "is_active": True,
        },
    )
    assert created.status_code == 201
    user = created.json()
    assert user["roles"] == ["registration"]

    updated = client.patch(
        f"/api/v1/users/{user['id']}",
        headers=auth_headers,
        json={"roles": ["registration", "pharmacy"], "is_active": False, "unlock": True},
    )
    assert updated.status_code == 200
    assert set(updated.json()["roles"]) == {"registration", "pharmacy"}
    assert updated.json()["is_active"] is False

    reset = client.post(
        f"/api/v1/users/{user['id']}/reset-password",
        headers=auth_headers,
        json={"password": "NewPass123!"},
    )
    assert reset.status_code == 200

    audits = client.get("/api/v1/audit-logs?action=USER_PASSWORD_RESET", headers=auth_headers)
    assert audits.status_code == 200
    assert audits.json()[0]["entity_id"] == user["id"]


def test_consent_research_withdrawal_is_audited(client: TestClient, auth_headers: dict[str, str]):
    patient_id = create_patient(client, auth_headers)
    created = client.post(
        f"/api/v1/patients/{patient_id}/consents",
        headers=auth_headers,
        json={
            "version": "2026-07",
            "method": "paper",
            "consented_at": datetime.now(timezone.utc).isoformat(),
            "staff_name": "Registration Staff",
            "service_consent": True,
            "research_consent": True,
            "notes": "Initial consent",
        },
    )
    assert created.status_code == 201
    consent = created.json()
    assert consent["consented_by"] is not None

    withdrawn = client.post(
        f"/api/v1/patients/{patient_id}/consents/{consent['id']}/withdraw-research",
        headers=auth_headers,
        json={"notes": "Patient requested withdrawal"},
    )
    assert withdrawn.status_code == 200
    body = withdrawn.json()
    assert body["research_consent"] is False
    assert body["research_withdrawn_at"] is not None
    assert body["withdrawn_by"] is not None

    audits = client.get("/api/v1/audit-logs?q=CONSENT_RESEARCH_WITHDRAWN", headers=auth_headers)
    assert audits.status_code == 200
    assert audits.json()[0]["entity_id"] == consent["id"]


def test_dashboard_summary_counts_current_system_state(client: TestClient, auth_headers: dict[str, str]):
    session_response = client.post(
        "/api/v1/clinic-sessions",
        headers=auth_headers,
        json={
            "name": "System Admin Clinic",
            "session_date": "2026-07-18",
            "start_time": "09:00:00",
            "end_time": "12:00:00",
            "location": "Campus",
            "owner": "CMRC",
            "status": "ACTIVE",
        },
    )
    assert session_response.status_code == 201
    patient_id = create_patient(client, auth_headers, "SYS-002")
    visit = client.post(
        "/api/v1/visits",
        headers=auth_headers,
        json={
            "clinic_session_id": session_response.json()["id"],
            "patient_id": patient_id,
            "registration_staff": "Registration Staff",
        },
    )
    assert visit.status_code == 201

    summary = client.get("/api/v1/dashboard/summary", headers=auth_headers)
    assert summary.status_code == 200
    body = summary.json()
    assert body["registered"] == 1
    assert body["active_sessions"] == 1
    assert body["patient_count"] == 1
    assert "inventory_available" in body


def test_audit_log_filters_limit_results(client: TestClient, auth_headers: dict[str, str], db_session: Session):
    admin = db_session.query(User).filter(User.username == "admin").one()
    db_session.add_all(
        [
            AuditLog(actor_user_id=admin.id, action="ONE", entity_type="sample", summary="first event"),
            AuditLog(actor_user_id=admin.id, action="TWO", entity_type="sample", summary="second event"),
            AuditLog(actor_user_id=admin.id, action="TWO", entity_type="other", summary="other event"),
        ]
    )
    db_session.commit()

    response = client.get("/api/v1/audit-logs?action=TWO&entity_type=sample&limit=1", headers=auth_headers)
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["action"] == "TWO"
    assert body[0]["entity_type"] == "sample"
