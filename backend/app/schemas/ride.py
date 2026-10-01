import uuid
from datetime import datetime

from geoalchemy2.shape import to_shape
from pydantic import BaseModel, Field

from app.models.ride import RideRequest, RideStatus


class Coordinates(BaseModel):
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)


class RideRequestCreate(BaseModel):
    pickup_address: str
    pickup: Coordinates
    destination_address: str
    destination: Coordinates
    departure_time: datetime
    time_flexibility_minutes: int = Field(default=20, ge=0, le=180)
    passenger_count: int = Field(default=1, ge=1, le=6)


class RideRequestUpdate(BaseModel):
    pickup_address: str | None = None
    pickup: Coordinates | None = None
    destination_address: str | None = None
    destination: Coordinates | None = None
    departure_time: datetime | None = None
    time_flexibility_minutes: int | None = Field(default=None, ge=0, le=180)
    passenger_count: int | None = Field(default=None, ge=1, le=6)


class RideRequestRead(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    pickup_address: str
    pickup: Coordinates
    destination_address: str
    destination: Coordinates
    departure_time: datetime
    time_flexibility_minutes: int
    passenger_count: int
    status: RideStatus
    created_at: datetime
    expires_at: datetime | None


def point_to_coordinates(point) -> Coordinates:
    shape = to_shape(point)
    return Coordinates(latitude=shape.y, longitude=shape.x)


def coordinates_to_ewkt(coordinates: Coordinates) -> str:
    return f"SRID=4326;POINT({coordinates.longitude} {coordinates.latitude})"


def ride_request_to_read(ride: RideRequest) -> RideRequestRead:
    return RideRequestRead(
        id=ride.id,
        user_id=ride.user_id,
        pickup_address=ride.pickup_address,
        pickup=point_to_coordinates(ride.pickup_point),
        destination_address=ride.destination_address,
        destination=point_to_coordinates(ride.destination_point),
        departure_time=ride.departure_time,
        time_flexibility_minutes=ride.time_flexibility_minutes,
        passenger_count=ride.passenger_count,
        status=ride.status,
        created_at=ride.created_at,
        expires_at=ride.expires_at,
    )
