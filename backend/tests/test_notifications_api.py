import uuid

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _register_and_login(email: str) -> dict[str, str]:
    client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "testpassword123", "display_name": "Notif Test"},
    )
    login = client.post("/api/v1/auth/login", json={"email": email, "password": "testpassword123"})
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


def _delete_user(email: str) -> None:
    from app.core.database import SessionLocal
    from app.models import User
    from sqlalchemy import select

    db = SessionLocal()
    try:
        user = db.scalar(select(User).where(User.email == email))
        if user is not None:
            db.delete(user)
            db.commit()
    finally:
        db.close()


@pytest.fixture
def user() -> dict[str, str]:
    email = f"{uuid.uuid4()}@stonybrook.edu"
    headers = _register_and_login(email)
    yield headers
    _delete_user(email)


def test_list_notifications_empty_initially(user: dict[str, str]) -> None:
    response = client.get("/api/v1/notifications", headers=user)
    assert response.status_code == 200
    assert response.json() == []


def test_mark_unknown_notification_read_is_404(user: dict[str, str]) -> None:
    response = client.patch(f"/api/v1/notifications/{uuid.uuid4()}/read", headers=user)
    assert response.status_code == 404
