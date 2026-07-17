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
from app.modules.auth.models import RefreshToken
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
        permission = Permission(code="users:manage", description="管理帳號")
        role = Role(name="admin", description="系統管理員", permissions=[permission])
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


def login(client: TestClient) -> dict:
    response = client.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": "ChangeMe123!"},
    )
    assert response.status_code == 200
    return response.json()


def test_login_returns_tokens_and_profile(client: TestClient):
    body = login(client)

    assert body["token_type"] == "bearer"
    assert body["access_token"]
    assert body["refresh_token"]
    assert body["user"]["username"] == "admin"
    assert body["user"]["roles"] == ["admin"]
    assert body["user"]["permissions"] == ["users:manage"]


def test_me_requires_valid_access_token(client: TestClient):
    token_body = login(client)

    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token_body['access_token']}"},
    )

    assert response.status_code == 200
    assert response.json()["email"] == "admin@example.com"


def test_refresh_rotates_refresh_token(client: TestClient, db_session: Session):
    token_body = login(client)

    response = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": token_body["refresh_token"]},
    )

    assert response.status_code == 200
    refreshed = response.json()
    assert refreshed["refresh_token"] != token_body["refresh_token"]
    revoked_tokens = db_session.query(RefreshToken).filter(RefreshToken.revoked_at.is_not(None)).all()
    assert len(revoked_tokens) == 1


def test_logout_revokes_refresh_token(client: TestClient, db_session: Session):
    token_body = login(client)

    response = client.post("/api/v1/auth/logout", json={"refresh_token": token_body["refresh_token"]})

    assert response.status_code == 204
    revoked_tokens = db_session.query(RefreshToken).filter(RefreshToken.revoked_at.is_not(None)).all()
    assert len(revoked_tokens) == 1


def test_invalid_password_increments_failed_login_count(client: TestClient, db_session: Session):
    response = client.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": "wrong-password"},
    )

    assert response.status_code == 401
    user = db_session.query(User).filter(User.username == "admin").one()
    assert user.failed_login_count == 1
