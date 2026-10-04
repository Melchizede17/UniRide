import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models import RideRequest, RideStatus, User
from app.schemas.match import MatchRead, match_to_read
from app.schemas.ride import (
    RideRequestCreate,
    RideRequestRead,
    RideRequestUpdate,
    coordinates_to_ewkt,
    ride_request_to_read,
)
from app.services import matching_service, notification_service, route_service

router = APIRouter(prefix="/rides", tags=["rides"])

ACTIVE_STATUSES = (RideStatus.ACTIVE, RideStatus.MATCH_PENDING, RideStatus.MATCHED)


def _get_owned_ride(ride_id: uuid.UUID, current_user: User, db: Session) -> RideRequest:
    ride = db.get(RideRequest, ride_id)
    if ride is None or ride.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ride request not found")
    return ride


@router.post("", response_model=RideRequestRead, status_code=status.HTTP_201_CREATED)
def create_ride_request(
    payload: RideRequestCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> RideRequestRead:
    ride = RideRequest(
        user_id=current_user.id,
        pickup_address=payload.pickup_address,
        pickup_point=coordinates_to_ewkt(payload.pickup),
        destination_address=payload.destination_address,
        destination_point=coordinates_to_ewkt(payload.destination),
        departure_time=payload.departure_time,
        time_flexibility_minutes=payload.time_flexibility_minutes,
        passenger_count=payload.passenger_count,
    )
    db.add(ride)
    db.commit()
    db.refresh(ride)

    route_service.refresh_route_for_ride(db, ride)
    db.commit()
    db.refresh(ride)

    return ride_request_to_read(ride)


@router.get("/me", response_model=list[RideRequestRead])
def list_my_active_rides(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> list[RideRequestRead]:
    rides = db.scalars(
        select(RideRequest)
        .where(RideRequest.user_id == current_user.id, RideRequest.status.in_(ACTIVE_STATUSES))
        .order_by(RideRequest.created_at.desc())
    ).all()
    return [ride_request_to_read(ride) for ride in rides]


@router.get("/history", response_model=list[RideRequestRead])
def list_my_ride_history(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> list[RideRequestRead]:
    rides = db.scalars(
        select(RideRequest).where(RideRequest.user_id == current_user.id).order_by(RideRequest.created_at.desc())
    ).all()
    return [ride_request_to_read(ride) for ride in rides]


@router.get("/{ride_id}", response_model=RideRequestRead)
def get_ride_request(
    ride_id: uuid.UUID, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> RideRequestRead:
    ride = _get_owned_ride(ride_id, current_user, db)
    return ride_request_to_read(ride)


@router.get("/{ride_id}/matches", response_model=list[MatchRead])
async def get_ride_matches(
    ride_id: uuid.UUID, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> list[MatchRead]:
    ride = _get_owned_ride(ride_id, current_user, db)
    if ride.status != RideStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ride is {ride.status.value} and not accepting new matches",
        )
    candidates = matching_service.find_matches(db, ride)
    matches, newly_created = matching_service.persist_suggested_matches(db, ride, candidates)

    for match in newly_created:
        other_ride = match.request_b if match.request_a_id == ride.id else match.request_a
        await notification_service.notify_user(
            db,
            other_ride.user_id,
            "MATCH_FOUND",
            f"A new ride match was found for your trip to {other_ride.destination_address}.",
            related_ride_id=other_ride.id,
        )

    return [match_to_read(match, current_user.id) for match in matches]


@router.patch("/{ride_id}", response_model=RideRequestRead)
def update_ride_request(
    ride_id: uuid.UUID,
    payload: RideRequestUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> RideRequestRead:
    ride = _get_owned_ride(ride_id, current_user, db)
    data = payload.model_dump(exclude_unset=True)

    location_changed = False
    if "pickup" in data:
        ride.pickup_point = coordinates_to_ewkt(payload.pickup)
        data.pop("pickup")
        location_changed = True
    if "destination" in data:
        ride.destination_point = coordinates_to_ewkt(payload.destination)
        data.pop("destination")
        location_changed = True

    for field, value in data.items():
        setattr(ride, field, value)

    db.commit()
    db.refresh(ride)

    if location_changed:
        route_service.refresh_route_for_ride(db, ride)
        db.commit()
        db.refresh(ride)

    return ride_request_to_read(ride)


@router.delete("/{ride_id}", status_code=status.HTTP_204_NO_CONTENT)
def cancel_ride_request(
    ride_id: uuid.UUID, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> None:
    ride = _get_owned_ride(ride_id, current_user, db)
    ride.status = RideStatus.CANCELLED
    db.commit()
