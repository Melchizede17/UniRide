import uuid
from datetime import datetime

from pydantic import BaseModel

from app.models.match import Match, MatchStatus
from app.schemas.ride import RideRequestRead, ride_request_to_read


class MatchRead(BaseModel):
    id: uuid.UUID
    my_ride_id: uuid.UUID
    other_ride: RideRequestRead
    destination_score: float
    time_score: float
    pickup_score: float
    preference_score: float
    route_overlap_score: float
    total_score: float
    status: MatchStatus
    created_at: datetime


def match_to_read(match: Match, current_user_id: uuid.UUID) -> MatchRead:
    if match.request_a.user_id == current_user_id:
        my_ride, other_ride = match.request_a, match.request_b
    else:
        my_ride, other_ride = match.request_b, match.request_a

    return MatchRead(
        id=match.id,
        my_ride_id=my_ride.id,
        other_ride=ride_request_to_read(other_ride),
        destination_score=match.destination_score,
        time_score=match.time_score,
        pickup_score=match.pickup_score,
        preference_score=match.preference_score,
        route_overlap_score=match.route_overlap_score,
        total_score=match.total_score,
        status=match.status,
        created_at=match.created_at,
    )
