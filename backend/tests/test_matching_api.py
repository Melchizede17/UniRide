import uuid
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.maps_service import RouteLookupError

client = TestClient(app)


def _register_and_login(email: str) -> dict[str, str]:
    client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "testpassword123", "display_name": "Match Test"},
    )
    login = client.post("/api/v1/auth/login", json={"email": email, "password": "testpassword123"})
    token = login.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


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
def two_users() -> tuple[dict[str, str], dict[str, str]]:
    email_a = f"{uuid.uuid4()}@stonybrook.edu"
    email_b = f"{uuid.uuid4()}@stonybrook.edu"
    headers_a = _register_and_login(email_a)
    headers_b = _register_and_login(email_b)
    yield headers_a, headers_b
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


def test_compatible_rides_match(two_users) -> None:
    headers_a, headers_b = two_users
    ride_a = _create_ride(headers_a)
    _create_ride(
        headers_b,
        pickup={"latitude": 40.9150, "longitude": -73.1240},  # ~100m from ride_a's pickup
        departure_time="2026-10-10T16:10:00",  # 10 min later, within combined 40 min window
    )

    matches_response = client.get(f"/api/v1/rides/{ride_a['id']}/matches", headers=headers_a)
    assert matches_response.status_code == 200, matches_response.text
    matches = matches_response.json()
    assert len(matches) == 1
    match = matches[0]
    assert match["status"] == "SUGGESTED"
    assert 0.0 < match["total_score"] <= 1.0
    assert match["pickup_score"] > 0.9
    assert match["time_score"] == pytest.approx(0.75, abs=0.01)
    # Both rides go Stony Brook -> JFK, so the real routed path should show
    # substantial overlap rather than falling back to the Phase 5 stand-in.
    assert match["route_overlap_score"] > 0.5


def test_far_destination_does_not_match(two_users) -> None:
    headers_a, headers_b = two_users
    ride_a = _create_ride(headers_a)
    _create_ride(
        headers_b,
        destination_address="Manhattan",
        destination={"latitude": 40.7831, "longitude": -73.9712},  # far from JFK
    )

    matches = client.get(f"/api/v1/rides/{ride_a['id']}/matches", headers=headers_a).json()
    assert matches == []


def test_require_same_gender_blocks_match_with_unknown_gender(two_users) -> None:
    headers_a, headers_b = two_users
    client.patch(
        "/api/v1/users/me/preferences", json={"gender_preference": "REQUIRE_SAME_GENDER"}, headers=headers_a
    )
    ride_a = _create_ride(headers_a)
    _create_ride(headers_b)

    matches = client.get(f"/api/v1/rides/{ride_a['id']}/matches", headers=headers_a).json()
    assert matches == []


def test_accept_both_sides_confirms_match_and_locks_rides(two_users) -> None:
    headers_a, headers_b = two_users
    ride_a = _create_ride(headers_a)
    ride_b = _create_ride(
        headers_b,
        pickup={"latitude": 40.9150, "longitude": -73.1240},
        departure_time="2026-10-10T16:10:00",
    )

    matches_a = client.get(f"/api/v1/rides/{ride_a['id']}/matches", headers=headers_a).json()
    match_id = matches_a[0]["id"]

    accept_a = client.post(f"/api/v1/matches/{match_id}/accept", headers=headers_a)
    assert accept_a.status_code == 200
    assert accept_a.json()["status"] == "A_ACCEPTED"
    assert accept_a.json()["accepted_by_me"] is True
    assert accept_a.json()["accepted_by_other"] is False

    # the other side, viewing the same match before responding, should see the mirror image
    pending_view_b = client.get(f"/api/v1/matches/{match_id}", headers=headers_b).json()
    assert pending_view_b["accepted_by_me"] is False
    assert pending_view_b["accepted_by_other"] is True

    accept_b = client.post(f"/api/v1/matches/{match_id}/accept", headers=headers_b)
    assert accept_b.status_code == 200
    assert accept_b.json()["status"] == "CONFIRMED"
    assert accept_b.json()["accepted_by_me"] is True
    assert accept_b.json()["accepted_by_other"] is True

    ride_a_after = client.get(f"/api/v1/rides/{ride_a['id']}", headers=headers_a).json()
    ride_b_after = client.get(f"/api/v1/rides/{ride_b['id']}", headers=headers_b).json()
    assert ride_a_after["status"] == "MATCHED"
    assert ride_b_after["status"] == "MATCHED"


def test_reject_match(two_users) -> None:
    headers_a, headers_b = two_users
    ride_a = _create_ride(headers_a)
    _create_ride(
        headers_b,
        pickup={"latitude": 40.9150, "longitude": -73.1240},
        departure_time="2026-10-10T16:10:00",
    )

    matches_a = client.get(f"/api/v1/rides/{ride_a['id']}/matches", headers=headers_a).json()
    match_id = matches_a[0]["id"]

    response = client.post(f"/api/v1/matches/{match_id}/reject", headers=headers_a)
    assert response.status_code == 200
    assert response.json()["status"] == "REJECTED"

    # Re-querying matches shouldn't resurrect the rejected pair as a fresh suggestion
    matches_after_reject = client.get(f"/api/v1/rides/{ride_a['id']}/matches", headers=headers_a).json()
    assert matches_after_reject == []


def test_cannot_accept_someone_elses_match(two_users) -> None:
    headers_a, headers_b = two_users
    ride_a = _create_ride(headers_a)
    _create_ride(
        headers_b,
        pickup={"latitude": 40.9150, "longitude": -73.1240},
        departure_time="2026-10-10T16:10:00",
    )
    matches_a = client.get(f"/api/v1/rides/{ride_a['id']}/matches", headers=headers_a).json()
    match_id = matches_a[0]["id"]

    email_c = f"{uuid.uuid4()}@stonybrook.edu"
    headers_c = _register_and_login(email_c)
    response = client.get(f"/api/v1/matches/{match_id}", headers=headers_c)
    assert response.status_code == 404
    _delete_user(email_c)


def test_route_lookup_failure_falls_back_to_distance_score(two_users) -> None:
    headers_a, headers_b = two_users
    ride_a = _create_ride(headers_a)

    with patch("app.services.route_service.get_route", side_effect=RouteLookupError("simulated failure")):
        _create_ride(
            headers_b,
            pickup={"latitude": 40.9150, "longitude": -73.1240},
            departure_time="2026-10-10T16:10:00",
        )

    matches = client.get(f"/api/v1/rides/{ride_a['id']}/matches", headers=headers_a).json()
    assert len(matches) == 1
    match = matches[0]
    assert match["route_overlap_score"] == 0.0
    assert 0.0 < match["total_score"] <= 1.0
