from dataclasses import dataclass

from geoalchemy2.shape import to_shape
from sqlalchemy import and_, or_, select, text
from sqlalchemy.orm import Session, selectinload

from app.matching import destination as destination_scoring
from app.matching import eligibility
from app.matching import pickup as pickup_scoring
from app.matching import preferences as preference_scoring
from app.matching import route_overlap as route_overlap_scoring
from app.matching import time as time_scoring
from app.matching.scorer import compute_total_score
from app.models import Match, MatchStatus, RideRequest, RideStatus, Route, User

# Fixed destination-distance threshold for eligibility (section 6.1's
# "destination_distance <= destination_threshold"). Also used as the Phase 5
# fallback score when either side lacks a routed Route yet.
DESTINATION_THRESHOLD_METERS = 5_000.0

# Corridor width for route-overlap: how far off either route counts as "on it".
OVERLAP_BUFFER_METERS = 250.0

MAX_CANDIDATES = 20


@dataclass
class MatchCandidate:
    ride_request: RideRequest
    destination_score: float
    time_score: float
    pickup_score: float
    preference_score: float
    route_overlap_score: float
    total_score: float


def _route_overlap_fraction(route_a: Route, route_b: Route, db: Session) -> float:
    wkt_a = to_shape(route_a.route_geometry).wkt
    wkt_b = to_shape(route_b.route_geometry).wkt
    row = db.execute(
        text(
            """
            SELECT
                ST_Length(ST_Intersection(ST_Buffer(ST_GeogFromText(:wkt_a), :buffer), ST_GeogFromText(:wkt_b))) AS b_in_a,
                ST_Length(ST_Intersection(ST_Buffer(ST_GeogFromText(:wkt_b), :buffer), ST_GeogFromText(:wkt_a))) AS a_in_b
            """
        ),
        {"wkt_a": wkt_a, "wkt_b": wkt_b, "buffer": OVERLAP_BUFFER_METERS},
    ).one()

    b_in_a_fraction = (row.b_in_a or 0.0) / route_b.distance_meters if route_b.distance_meters else 0.0
    a_in_b_fraction = (row.a_in_b or 0.0) / route_a.distance_meters if route_a.distance_meters else 0.0
    return (b_in_a_fraction + a_in_b_fraction) / 2


def find_matches(db: Session, ride: RideRequest) -> list[MatchCandidate]:
    requester = ride.user
    requester_prefs = requester.preferences

    pickup_distance = RideRequest.pickup_point.ST_Distance(ride.pickup_point).label("pickup_distance")
    destination_distance = RideRequest.destination_point.ST_Distance(ride.destination_point).label(
        "destination_distance"
    )

    rows = db.execute(
        select(RideRequest, pickup_distance, destination_distance)
        .options(
            selectinload(RideRequest.user).selectinload(User.preferences),
            selectinload(RideRequest.route),
        )
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

        if ride.route is not None and candidate_ride.route is not None:
            overlap_fraction = _route_overlap_fraction(ride.route, candidate_ride.route, db)
            time_detour = time_diff_minutes / allowed_window
            distance_detour = pickup_distance_m / ride.route.distance_meters if ride.route.distance_meters else 0.0
            d_score = route_overlap_scoring.score(overlap_fraction, time_detour, distance_detour)
            overlap_score = overlap_fraction
        else:
            # Fall back to Phase 5's distance-based stand-in when either side
            # hasn't been routed yet (Maps API failure/pending).
            d_score = destination_scoring.score(destination_distance_m, DESTINATION_THRESHOLD_METERS)
            overlap_score = 0.0

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
                route_overlap_score=overlap_score,
                total_score=compute_total_score(d_score, t_score, p_score, g_score),
            )
        )

    candidates.sort(key=lambda c: c.total_score, reverse=True)
    return candidates[:MAX_CANDIDATES]


REJECTED_STATUSES = (MatchStatus.REJECTED, MatchStatus.CANCELLED, MatchStatus.EXPIRED)


def persist_suggested_matches(
    db: Session, ride: RideRequest, candidates: list[MatchCandidate]
) -> tuple[list[Match], list[Match]]:
    """Returns (all_matches, newly_created_matches) - the latter for callers
    that want to notify the other side only once, not on every re-query."""
    matches: list[Match] = []
    newly_created: list[Match] = []
    for candidate in candidates:
        other_id = candidate.ride_request.id
        existing = db.scalar(
            select(Match).where(
                or_(
                    and_(Match.request_a_id == ride.id, Match.request_b_id == other_id),
                    and_(Match.request_a_id == other_id, Match.request_b_id == ride.id),
                )
            )
        )

        if existing is not None and existing.status in REJECTED_STATUSES:
            # Already rejected/cancelled once: don't resurrect it as a fresh
            # SUGGESTED match just because the candidate still scores well.
            continue

        if existing is None:
            existing = Match(request_a_id=ride.id, request_b_id=other_id)
            db.add(existing)
            newly_created.append(existing)

        existing.destination_score = candidate.destination_score
        existing.time_score = candidate.time_score
        existing.pickup_score = candidate.pickup_score
        existing.preference_score = candidate.preference_score
        existing.route_overlap_score = candidate.route_overlap_score
        existing.total_score = candidate.total_score
        matches.append(existing)

    db.commit()
    matches.sort(key=lambda m: m.total_score, reverse=True)
    return matches, newly_created
