import uuid

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _register_and_login(email: str) -> tuple[dict[str, str], str]:
    client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "testpassword123", "display_name": "RT Test"},
    )
    login = client.post("/api/v1/auth/login", json={"email": email, "password": "testpassword123"})
    token = login.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}, token


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
def two_users() -> tuple[tuple[dict[str, str], str], tuple[dict[str, str], str]]:
    email_a = f"{uuid.uuid4()}@stonybrook.edu"
    email_b = f"{uuid.uuid4()}@stonybrook.edu"
    user_a = _register_and_login(email_a)
    user_b = _register_and_login(email_b)
    yield user_a, user_b
    _delete_user(email_a)
    _delete_user(email_b)


def _create_ride(headers: dict[str, str], **overrides) -> dict:
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
    response = client.post("/api/v1/rides", json=payload, headers=headers)
    assert response.status_code == 201, response.text
    return response.json()


def test_new_match_notifies_the_other_rider_live(two_users) -> None:
    (headers_a, token_a), (headers_b, token_b) = two_users
    ride_a = _create_ride(headers_a)
    _create_ride(
        headers_b,
        pickup={"latitude": 40.9150, "longitude": -73.1240},
        departure_time="2026-10-10T16:10:00",
    )

    with client.websocket_connect(f"/api/v1/ws/matches?token={token_b}") as ws_b:
        matches = client.get(f"/api/v1/rides/{ride_a['id']}/matches", headers=headers_a).json()
        assert len(matches) == 1

        event = ws_b.receive_json()
        assert event["event"] == "notification"
        assert event["data"]["type"] == "MATCH_FOUND"
        assert event["data"]["is_read"] is False

    notifications_b = client.get("/api/v1/notifications", headers=headers_b).json()
    assert len(notifications_b) == 1
    assert notifications_b[0]["type"] == "MATCH_FOUND"

    notifications_a = client.get("/api/v1/notifications", headers=headers_a).json()
    assert notifications_a == []  # the searcher doesn't notify themselves


def test_requerying_matches_does_not_renotify(two_users) -> None:
    (headers_a, _), (headers_b, _) = two_users
    ride_a = _create_ride(headers_a)
    _create_ride(
        headers_b,
        pickup={"latitude": 40.9150, "longitude": -73.1240},
        departure_time="2026-10-10T16:10:00",
    )

    client.get(f"/api/v1/rides/{ride_a['id']}/matches", headers=headers_a)
    client.get(f"/api/v1/rides/{ride_a['id']}/matches", headers=headers_a)

    notifications_b = client.get("/api/v1/notifications", headers=headers_b).json()
    assert len(notifications_b) == 1


def test_accept_notifies_other_side_then_confirm_notifies_both(two_users) -> None:
    (headers_a, token_a), (headers_b, token_b) = two_users
    ride_a = _create_ride(headers_a)
    _create_ride(
        headers_b,
        pickup={"latitude": 40.9150, "longitude": -73.1240},
        departure_time="2026-10-10T16:10:00",
    )
    with client.websocket_connect(f"/api/v1/ws/matches?token={token_b}") as ws_b:
        match_id = client.get(f"/api/v1/rides/{ride_a['id']}/matches", headers=headers_a).json()[0]["id"]
        ws_b.receive_json()  # MATCH_FOUND from the search above

        client.post(f"/api/v1/matches/{match_id}/accept", headers=headers_a)
        accepted_event = ws_b.receive_json()
        assert accepted_event["data"]["type"] == "MATCH_ACCEPTED"

        with client.websocket_connect(f"/api/v1/ws/matches?token={token_a}") as ws_a:
            client.post(f"/api/v1/matches/{match_id}/accept", headers=headers_b)
            confirmed_event_a = ws_a.receive_json()
            confirmed_event_b = ws_b.receive_json()
            assert confirmed_event_a["data"]["type"] == "MATCH_CONFIRMED"
            assert confirmed_event_b["data"]["type"] == "MATCH_CONFIRMED"


def test_reject_notifies_other_side(two_users) -> None:
    (headers_a, token_a), (headers_b, token_b) = two_users
    ride_a = _create_ride(headers_a)
    _create_ride(
        headers_b,
        pickup={"latitude": 40.9150, "longitude": -73.1240},
        departure_time="2026-10-10T16:10:00",
    )
    with client.websocket_connect(f"/api/v1/ws/matches?token={token_b}") as ws_b:
        match_id = client.get(f"/api/v1/rides/{ride_a['id']}/matches", headers=headers_a).json()[0]["id"]
        ws_b.receive_json()  # MATCH_FOUND

        client.post(f"/api/v1/matches/{match_id}/reject", headers=headers_a)
        rejected_event = ws_b.receive_json()
        assert rejected_event["data"]["type"] == "MATCH_REJECTED"
