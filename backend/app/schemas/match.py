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
    accepted_by_me: bool
    accepted_by_other: bool
    created_at: datetime


def match_to_read(match: Match, current_user_id: uuid.UUID) -> MatchRead:
    is_a = match.request_a.user_id == current_user_id
    my_ride, other_ride = (match.request_a, match.request_b) if is_a else (match.request_b, match.request_a)

    if match.status == MatchStatus.CONFIRMED:
        accepted_by_me = accepted_by_other = True
    elif match.status == MatchStatus.A_ACCEPTED:
        accepted_by_me, accepted_by_other = is_a, not is_a
    elif match.status == MatchStatus.B_ACCEPTED:
        accepted_by_me, accepted_by_other = not is_a, is_a
    else:
        accepted_by_me = accepted_by_other = False

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
        accepted_by_me=accepted_by_me,
        accepted_by_other=accepted_by_other,
        created_at=match.created_at,
    )
