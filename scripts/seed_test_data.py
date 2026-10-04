"""Generates a synthetic ride-request dataset for evaluating the matching
engine (architecture doc Phase 8 / section 20).

Run standalone to seed the dev DB and leave the data there for manual
exploration (e.g. via /docs or the frontend):
    python scripts/seed_test_data.py
    python scripts/seed_test_data.py --cleanup   # remove it again

Importing seed_dataset()/clear_synthetic_data() directly (as
evaluate_matching.py does) lets a caller manage the session and lifecycle
itself - e.g. seed, measure, then clean up in one run, so this dataset never
lingers in the same dev DB the pytest suite also runs against.
"""

import random
import sys
import uuid
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from sqlalchemy import select  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

from app.core.database import SessionLocal  # noqa: E402
from app.core.security import hash_password  # noqa: E402
from app.models import GenderPreference, RideRequest, User, UserPreference  # noqa: E402
from app.schemas.ride import Coordinates, coordinates_to_ewkt  # noqa: E402
from app.services import route_service  # noqa: E402

EMAIL_PREFIX = "synthetic-"
SYNTHETIC_PASSWORD = "synthetic-dataset-password"
NUM_REQUESTS = 40
DEMO_DATE = datetime(2026, 10, 10)

# (name, lat, lng) - real NYC-area destinations students from Stony Brook
# plausibly travel to, per section 2 of the architecture doc ("airports,
# train stations, shopping areas, or other regional destinations").
DESTINATIONS = [
    ("JFK Airport", 40.6413, -73.7781),
    ("LaGuardia Airport", 40.7769, -73.8740),
    ("Penn Station, Manhattan", 40.7506, -73.9935),
    ("Times Square, Manhattan", 40.7580, -73.9855),
    ("Smith Haven Mall", 40.8829, -73.1500),
]

# (name, lat, lng) - plausible on/near-campus pickup anchors.
PICKUP_ANCHORS = [
    ("Stony Brook University", 40.9143, -73.1234),
    ("Stony Brook Train Station", 40.9138, -73.1409),
    ("West Campus Residence Halls", 40.9117, -73.1264),
    ("Stony Brook Village Apartments", 40.9239, -73.1409),
]

GENDER_PREFERENCE_WEIGHTS = [
    (GenderPreference.NO_PREFERENCE, 0.70),
    (GenderPreference.PREFER_SAME_GENDER, 0.20),
    (GenderPreference.REQUIRE_SAME_GENDER, 0.10),
]

TIME_FLEXIBILITY_CHOICES = [10, 15, 20, 30]
GENDERS = ["female", "male"]


def jitter(lat: float, lng: float, max_meters: float, rng: random.Random) -> tuple[float, float]:
    # ~111,320 meters per degree of latitude; good enough approximation for jitter at this scale.
    meters_per_degree = 111_320
    offset_lat = rng.uniform(-max_meters, max_meters) / meters_per_degree
    offset_lng = rng.uniform(-max_meters, max_meters) / (meters_per_degree * 0.76)  # cos(~40.9 deg lat)
    return lat + offset_lat, lng + offset_lng


def weighted_choice(choices: list[tuple], rng: random.Random):
    values, weights = zip(*choices)
    return rng.choices(values, weights=weights, k=1)[0]


def build_departure_slots(rng: random.Random) -> list[datetime]:
    """A handful of shared time clusters (so some requests can actually match
    each other) plus implicit outliers from the per-request jitter below."""
    slots = []
    for hour in (8, 12, 16, 18):
        for _ in range(2):
            slots.append(DEMO_DATE.replace(hour=hour, minute=rng.choice([0, 15, 30, 45])))
    return slots


def clear_synthetic_data(db: Session) -> int:
    existing = db.scalars(select(User).where(User.email.like(f"{EMAIL_PREFIX}%"))).all()
    count = len(existing)
    for user in existing:
        db.delete(user)
    db.commit()
    return count


def seed_dataset(db: Session, verbose: bool = True) -> list[RideRequest]:
    """Clears any previous synthetic data, then creates a fresh dataset.
    Returns the created RideRequest rows (already committed, routes fetched)."""
    removed = clear_synthetic_data(db)
    if removed and verbose:
        print(f"Cleared {removed} existing synthetic users.")

    rng = random.Random(42)  # fixed seed: reruns produce the same dataset
    departure_slots = build_departure_slots(rng)
    password_hash = hash_password(SYNTHETIC_PASSWORD)

    rides: list[RideRequest] = []
    for i in range(NUM_REQUESTS):
        destination_name, dest_lat, dest_lng = rng.choice(DESTINATIONS)
        pickup_name, pickup_lat, pickup_lng = rng.choice(PICKUP_ANCHORS)

        pickup_lat_j, pickup_lng_j = jitter(pickup_lat, pickup_lng, max_meters=800, rng=rng)
        dest_lat_j, dest_lng_j = jitter(dest_lat, dest_lng, max_meters=300, rng=rng)

        # ~85% land in a shared time slot (so matches are possible); ~15% are
        # standalone outliers, so the evaluation also sees requests that
        # legitimately get zero matches.
        if rng.random() < 0.85:
            departure_time = rng.choice(departure_slots) + timedelta(minutes=rng.randint(-10, 10))
        else:
            departure_time = DEMO_DATE.replace(hour=rng.randint(6, 22), minute=rng.randint(0, 59))

        user = User(
            id=uuid.uuid4(),
            email=f"{EMAIL_PREFIX}{i:03d}@stonybrook.edu",
            password_hash=password_hash,
            display_name=f"Synthetic Rider {i:03d}",
            university="Stony Brook University",
            email_verified=True,
            gender=rng.choice(GENDERS),
        )
        db.add(user)
        db.flush()

        db.add(
            UserPreference(
                user_id=user.id,
                gender_preference=weighted_choice(GENDER_PREFERENCE_WEIGHTS, rng),
            )
        )

        ride = RideRequest(
            user_id=user.id,
            pickup_address=pickup_name,
            pickup_point=coordinates_to_ewkt(Coordinates(latitude=pickup_lat_j, longitude=pickup_lng_j)),
            destination_address=destination_name,
            destination_point=coordinates_to_ewkt(Coordinates(latitude=dest_lat_j, longitude=dest_lng_j)),
            departure_time=departure_time,
            time_flexibility_minutes=rng.choice(TIME_FLEXIBILITY_CHOICES),
            passenger_count=rng.choice([1, 1, 1, 2]),
        )
        db.add(ride)
        db.commit()
        db.refresh(ride)

        route = route_service.refresh_route_for_ride(db, ride)
        db.commit()
        db.refresh(ride)

        rides.append(ride)
        if verbose:
            status = "routed" if route is not None else "no route (fallback scoring)"
            print(f"  [{i + 1}/{NUM_REQUESTS}] {user.email}: {pickup_name} -> {destination_name} ({status})")

    if verbose:
        print(f"\nSeeded {len(rides)} synthetic ride requests.")
    return rides


def main() -> None:
    db = SessionLocal()
    try:
        if "--cleanup" in sys.argv:
            removed = clear_synthetic_data(db)
            print(f"Removed {removed} synthetic users.")
            return
        seed_dataset(db)
        print("\nData left in place. Run with --cleanup to remove it.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
