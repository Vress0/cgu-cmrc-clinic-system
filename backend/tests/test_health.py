from fastapi.testclient import TestClient

from app.api.v1 import health
from app.main import create_app


def test_health_check_ok(monkeypatch):
    monkeypatch.setattr(health, "check_database", lambda: True)
    client = TestClient(create_app())

    response = client.get("/api/v1/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["database"] == "ok"
    assert body["service"] == "backend"


def test_health_check_degraded_when_database_unavailable(monkeypatch):
    monkeypatch.setattr(health, "check_database", lambda: False)
    client = TestClient(create_app())

    response = client.get("/api/v1/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "degraded"
    assert body["database"] == "unavailable"
