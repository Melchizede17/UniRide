import logging

from geoalchemy2.shape import to_shape
from sqlalchemy.orm import Session

from app.models import RideRequest, Route
from app.services.maps_service import RouteLookupError, get_route

logger = logging.getLogger(__name__)


def _points_to_linestring_ewkt(points: list[tuple[float, float]]) -> str:
    coords = ", ".join(f"{lng} {lat}" for lat, lng in points)
    return f"SRID=4326;LINESTRING({coords})"


def refresh_route_for_ride(db: Session, ride: RideRequest) -> Route | None:
    """Fetches and upserts the Route row for a ride request. Best-effort: if the
    routing provider fails (no key, quota, no route found), logs and returns
    None rather than raising, so ride creation/update never fails on a Maps
    API hiccup. Matching falls back to the Phase 5 distance-based score for
    any ride missing a Route.
    """
    pickup = to_shape(ride.pickup_point)
    destination = to_shape(ride.destination_point)

    try:
        result = get_route(pickup.y, pickup.x, destination.y, destination.x)
    except RouteLookupError:
        logger.warning("Route lookup failed for ride %s", ride.id, exc_info=True)
        return None

    route = ride.route
    if route is None:
        route = Route(ride_request_id=ride.id, provider="google_routes_v2")
        db.add(route)

    route.route_geometry = _points_to_linestring_ewkt(result["points"])
    route.distance_meters = result["distance_meters"]
    route.duration_seconds = result["duration_seconds"]
    route.provider = "google_routes_v2"

    db.flush()
    return route
