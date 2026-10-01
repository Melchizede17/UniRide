import uuid

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


@pytest.fixture
def auth_headers() -> dict[str, str]:
    email = f"{uuid.uuid4()}@stonybrook.edu"
    password = "testpassword123"

    register_response = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password, "display_name": "Test Student"},
    )
    assert register_response.status_code == 201, register_response.text

    login_response = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert login_response.status_code == 200, login_response.text
    token = login_response.json()["access_token"]

    headers = {"Authorization": f"Bearer {token}"}
    yield headers

    me = client.get("/api/v1/auth/me", headers=headers).json()
    from app.core.database import SessionLocal
    from app.models import User

    db = SessionLocal()
    try:
        user = db.get(User, uuid.UUID(me["id"]))
        if user is not None:
            db.delete(user)
            db.commit()
    finally:
        db.close()


def _ride_payload(**overrides) -> dict:
    payload = {
        "pickup_address": "Stony Brook University",
        "pickup": {"latitude": 40.9143, "longitude": -73.1234},
        "destination_address": "JFK Airport",
        "destination": {"latitude": 40.6413, "longitude": -73.7781},
        "departure_time": "2026-10-10T16:00:00",
        "time_flexibility_minutes": 20,
        "passenger_count": 1,
    }
    payload.update(overrides)
    return payload


def test_register_requires_unique_email(auth_headers: dict[str, str]) -> None:
    me = client.get("/api/v1/auth/me", headers=auth_headers).json()
    response = client.post(
        "/api/v1/auth/register",
        json={"email": me["email"], "password": "anotherpassword", "display_name": "Dup"},
    )
    assert response.status_code == 400


def test_login_rejects_wrong_password(auth_headers: dict[str, str]) -> None:
    me = client.get("/api/v1/auth/me", headers=auth_headers).json()
    response = client.post("/api/v1/auth/login", json={"email": me["email"], "password": "wrong"})
    assert response.status_code == 401


def test_unauthenticated_request_rejected() -> None:
    response = client.get("/api/v1/rides/me")
    assert response.status_code == 401


def test_ride_crud_lifecycle(auth_headers: dict[str, str]) -> None:
    create_response = client.post("/api/v1/rides", json=_ride_payload(), headers=auth_headers)
    assert create_response.status_code == 201, create_response.text
    ride = create_response.json()
    assert ride["status"] == "ACTIVE"
    assert ride["pickup"]["latitude"] == pytest.approx(40.9143)
    assert ride["destination"]["longitude"] == pytest.approx(-73.7781)

    ride_id = ride["id"]

    get_response = client.get(f"/api/v1/rides/{ride_id}", headers=auth_headers)
    assert get_response.status_code == 200
    assert get_response.json()["id"] == ride_id

    list_response = client.get("/api/v1/rides/me", headers=auth_headers)
    assert list_response.status_code == 200
    assert any(r["id"] == ride_id for r in list_response.json())

    update_response = client.patch(
        f"/api/v1/rides/{ride_id}", json={"passenger_count": 3}, headers=auth_headers
    )
    assert update_response.status_code == 200
    assert update_response.json()["passenger_count"] == 3

    delete_response = client.delete(f"/api/v1/rides/{ride_id}", headers=auth_headers)
    assert delete_response.status_code == 204

    active_list = client.get("/api/v1/rides/me", headers=auth_headers).json()
    assert all(r["id"] != ride_id for r in active_list)

    history_list = client.get("/api/v1/rides/history", headers=auth_headers).json()
    cancelled = next(r for r in history_list if r["id"] == ride_id)
    assert cancelled["status"] == "CANCELLED"


def test_cannot_access_another_users_ride(auth_headers: dict[str, str]) -> None:
    create_response = client.post("/api/v1/rides", json=_ride_payload(), headers=auth_headers)
    ride_id = create_response.json()["id"]

    other_email = f"{uuid.uuid4()}@stonybrook.edu"
    client.post(
        "/api/v1/auth/register",
        json={"email": other_email, "password": "testpassword123", "display_name": "Other Student"},
    )
    other_login = client.post(
        "/api/v1/auth/login", json={"email": other_email, "password": "testpassword123"}
    )
    other_headers = {"Authorization": f"Bearer {other_login.json()['access_token']}"}

    response = client.get(f"/api/v1/rides/{ride_id}", headers=other_headers)
    assert response.status_code == 404

    other_me = client.get("/api/v1/auth/me", headers=other_headers).json()
    from app.core.database import SessionLocal
    from app.models import User

    db = SessionLocal()
    try:
        user = db.get(User, uuid.UUID(other_me["id"]))
        if user is not None:
            db.delete(user)
            db.commit()
    finally:
        db.close()
