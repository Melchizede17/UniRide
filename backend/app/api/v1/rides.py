import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models import RideRequest, RideStatus, User
from app.schemas.ride import (
    RideRequestCreate,
    RideRequestRead,
    RideRequestUpdate,
    coordinates_to_ewkt,
    ride_request_to_read,
)

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


@router.patch("/{ride_id}", response_model=RideRequestRead)
def update_ride_request(
    ride_id: uuid.UUID,
    payload: RideRequestUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> RideRequestRead:
    ride = _get_owned_ride(ride_id, current_user, db)
    data = payload.model_dump(exclude_unset=True)

    if "pickup" in data:
        ride.pickup_point = coordinates_to_ewkt(payload.pickup)
        data.pop("pickup")
    if "destination" in data:
        ride.destination_point = coordinates_to_ewkt(payload.destination)
        data.pop("destination")

    for field, value in data.items():
        setattr(ride, field, value)

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
