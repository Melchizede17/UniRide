from dataclasses import dataclass

from sqlalchemy import and_, or_, select
from sqlalchemy.orm import Session, selectinload

from app.matching import destination as destination_scoring
from app.matching import eligibility
from app.matching import pickup as pickup_scoring
from app.matching import preferences as preference_scoring
from app.matching import time as time_scoring
from app.matching.scorer import compute_total_score
from app.models import Match, MatchStatus, RideRequest, RideStatus, User

# Phase 5 stand-in for true route feasibility (section 6.2, Phase 6): a fixed
# destination-distance threshold, per section 6.1's "destination_distance <=
# destination_threshold". Not yet configurable/learned (see scorer.py).
DESTINATION_THRESHOLD_METERS = 5_000.0

MAX_CANDIDATES = 20


@dataclass
class MatchCandidate:
    ride_request: RideRequest
    destination_score: float
    time_score: float
    pickup_score: float
    preference_score: float
    total_score: float


def find_matches(db: Session, ride: RideRequest) -> list[MatchCandidate]:
    requester = ride.user
    requester_prefs = requester.preferences

    pickup_distance = RideRequest.pickup_point.ST_Distance(ride.pickup_point).label("pickup_distance")
    destination_distance = RideRequest.destination_point.ST_Distance(ride.destination_point).label(
        "destination_distance"
    )

    rows = db.execute(
        select(RideRequest, pickup_distance, destination_distance)
        .options(selectinload(RideRequest.user).selectinload(User.preferences))
        .where(
            RideRequest.id != ride.id,
            RideRequest.user_id != ride.user_id,
            RideRequest.status == RideStatus.ACTIVE,
            RideRequest.destination_point.ST_DWithin(ride.destination_point, DESTINATION_THRESHOLD_METERS),
        )
    ).all()

    candidates: list[MatchCandidate] = []
    for candidate_ride, pickup_distance_m, destination_distance_m in rows:
        candidate_user = candidate_ride.user
        candidate_prefs = candidate_user.preferences

        pickup_radius = min(
            requester_prefs.default_pickup_radius_meters, candidate_prefs.default_pickup_radius_meters
        )
        if not eligibility.is_pickup_feasible(pickup_distance_m, pickup_radius):
            continue

        time_diff_minutes = abs((ride.departure_time - candidate_ride.departure_time).total_seconds()) / 60
        allowed_window = max(1, ride.time_flexibility_minutes + candidate_ride.time_flexibility_minutes)
        if not eligibility.is_time_compatible(time_diff_minutes, allowed_window):
            continue

        if not preference_scoring.is_mutually_eligible(
            requester.gender, requester_prefs.gender_preference, candidate_user.gender, candidate_prefs.gender_preference
        ):
            continue

        d_score = destination_scoring.score(destination_distance_m, DESTINATION_THRESHOLD_METERS)
        t_score = time_scoring.score(time_diff_minutes, allowed_window)
        p_score = pickup_scoring.score(pickup_distance_m, pickup_radius)
        g_score = preference_scoring.score(
            requester.gender, requester_prefs.gender_preference, candidate_user.gender, candidate_prefs.gender_preference
        )

        candidates.append(
            MatchCandidate(
                ride_request=candidate_ride,
                destination_score=d_score,
                time_score=t_score,
                pickup_score=p_score,
                preference_score=g_score,
                total_score=compute_total_score(d_score, t_score, p_score, g_score),
            )
        )

    candidates.sort(key=lambda c: c.total_score, reverse=True)
    return candidates[:MAX_CANDIDATES]


def persist_suggested_matches(db: Session, ride: RideRequest, candidates: list[MatchCandidate]) -> list[Match]:
    matches: list[Match] = []
    for candidate in candidates:
        other_id = candidate.ride_request.id
        existing = db.scalar(
            select(Match).where(
                or_(
                    and_(Match.request_a_id == ride.id, Match.request_b_id == other_id),
                    and_(Match.request_a_id == other_id, Match.request_b_id == ride.id),
                ),
                Match.status.in_((MatchStatus.SUGGESTED, MatchStatus.A_ACCEPTED, MatchStatus.B_ACCEPTED)),
            )
        )
        if existing is None:
            existing = Match(request_a_id=ride.id, request_b_id=other_id, route_overlap_score=0.0)
            db.add(existing)

        existing.destination_score = candidate.destination_score
        existing.time_score = candidate.time_score
        existing.pickup_score = candidate.pickup_score
        existing.preference_score = candidate.preference_score
        existing.total_score = candidate.total_score
        matches.append(existing)

    db.commit()
    matches.sort(key=lambda m: m.total_score, reverse=True)
    return matches
