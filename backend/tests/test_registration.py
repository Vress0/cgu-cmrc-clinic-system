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
            Permission(code="sessions:manage", description="管理義診場次"),
            Permission(code="patients:read", description="查看個案"),
            Permission(code="patients:write", description="修改個案"),
            Permission(code="visits:manage", description="管理掛號"),
        ]
        role = Role(name="admin", description="系統管理員", permissions=permissions)
        user = User(
            username="admin",
            email="admin@example.com",
            full_name="系統管理員",
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
            "name": "2026 夏季義診",
            "session_date": "2026-07-17",
            "start_time": "09:00:00",
            "end_time": "12:00:00",
            "location": "長庚大學",
            "owner": "社長",
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
            "case_number": "CGU-0001",
            "name": "王小明",
            "sex": "MALE",
            "birth_date": "1950-01-01",
            "phone": "0900000000",
            "primary_language": "台語",
            "assistance_needs": "需要台語協助",
        },
    )
    assert response.status_code == 201
    return response.json()["id"]


def test_registration_flow(client: TestClient, auth_headers: dict[str, str]):
    session_id = create_session(client, auth_headers)
    patient_id = create_patient(client, auth_headers)

    history_response = client.put(
        f"/api/v1/patients/{patient_id}/health-history",
        headers=auth_headers,
        json={"chronic_diseases": "高血壓", "allergies": "青黴素"},
    )
    assert history_response.status_code == 200
    assert history_response.json()["allergies"] == "青黴素"

    consent_response = client.post(
        f"/api/v1/patients/{patient_id}/consents",
        headers=auth_headers,
        json={
            "version": "v1",
            "method": "口頭同意",
            "consented_at": datetime.now(timezone.utc).isoformat(),
            "staff_name": "掛號人員",
            "service_consent": True,
            "research_consent": False,
        },
    )
    assert consent_response.status_code == 201

    visit_response = client.post(
        "/api/v1/visits",
        headers=auth_headers,
        json={
            "clinic_session_id": session_id,
            "patient_id": patient_id,
            "registration_staff": "掛號人員",
        },
    )
    assert visit_response.status_code == 201
    visit = visit_response.json()
    assert visit["queue_number"] == 1
    assert visit["status"] == "REGISTERED"

    next_status_response = client.patch(
        f"/api/v1/visits/{visit['id']}/status",
        headers=auth_headers,
        json={"status": "WAITING_FOR_CLINIC"},
    )
    assert next_status_response.status_code == 200
    assert next_status_response.json()["status"] == "WAITING_FOR_CLINIC"


def test_prevent_duplicate_visit_in_same_session(client: TestClient, auth_headers: dict[str, str]):
    session_id = create_session(client, auth_headers)
    patient_id = create_patient(client, auth_headers)
    payload = {
        "clinic_session_id": session_id,
        "patient_id": patient_id,
        "registration_staff": "掛號人員",
    }

    first = client.post("/api/v1/visits", headers=auth_headers, json=payload)
    second = client.post("/api/v1/visits", headers=auth_headers, json=payload)

    assert first.status_code == 201
    assert second.status_code == 409


def test_registration_api_requires_login(client: TestClient):
    response = client.get("/api/v1/patients")

    assert response.status_code == 401
