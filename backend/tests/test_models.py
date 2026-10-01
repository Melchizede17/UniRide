import uuid
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models import GenderPreference, RideRequest, RideStatus, User, UserPreference


@pytest.fixture
def db() -> Session:
    session = SessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


def test_create_user_with_preferences_and_ride_request(db: Session) -> None:
    user = User(
        email=f"{uuid.uuid4()}@stonybrook.edu",
        password_hash="hashed",
        display_name="Test Student",
        university="Stony Brook University",
    )
    db.add(user)
    db.flush()

    user.preferences = UserPreference(gender_preference=GenderPreference.PREFER_SAME_GENDER)
    db.add(user.preferences)

    ride = RideRequest(
        user_id=user.id,
        pickup_address="Stony Brook University",
        pickup_point="SRID=4326;POINT(-73.1234 40.9143)",
        destination_address="JFK Airport",
        destination_point="SRID=4326;POINT(-73.7781 40.6413)",
        departure_time=datetime.now(timezone.utc) + timedelta(hours=1),
        time_flexibility_minutes=20,
    )
    db.add(ride)
    db.flush()

    fetched = db.get(User, user.id)
    assert fetched is not None
    assert fetched.preferences.gender_preference == GenderPreference.PREFER_SAME_GENDER
    assert fetched.ride_requests[0].status == RideStatus.ACTIVE
