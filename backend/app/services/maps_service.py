import logging

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

ROUTES_API_URL = "https://routes.googleapis.com/directions/v2:computeRoutes"


class RouteLookupError(Exception):
    pass


def decode_polyline(encoded: str) -> list[tuple[float, float]]:
    """Decodes Google's Encoded Polyline Algorithm Format into (lat, lng) pairs."""
    points: list[tuple[float, float]] = []
    index = lat = lng = 0

    while index < len(encoded):
        for is_lat in (True, False):
            shift = result = 0
            while True:
                byte = ord(encoded[index]) - 63
                index += 1
                result |= (byte & 0x1F) << shift
                shift += 5
                if byte < 0x20:
                    break
            delta = ~(result >> 1) if result & 1 else result >> 1
            if is_lat:
                lat += delta
            else:
                lng += delta
        points.append((lat / 1e5, lng / 1e5))

    return points


def get_route(origin_lat: float, origin_lng: float, destination_lat: float, destination_lng: float) -> dict:
    """Fetches a driving route from Google Routes API v2.

    Returns {"distance_meters": int, "duration_seconds": int, "points": [(lat, lng), ...]}.
    Raises RouteLookupError on any failure (no key configured, request denied, no route found).
    """
    if not settings.google_maps_api_key:
        raise RouteLookupError("GOOGLE_MAPS_API_KEY is not configured")

    body = {
        "origin": {"location": {"latLng": {"latitude": origin_lat, "longitude": origin_lng}}},
        "destination": {"location": {"latLng": {"latitude": destination_lat, "longitude": destination_lng}}},
        "travelMode": "DRIVE",
    }
    try:
        response = httpx.post(
            ROUTES_API_URL,
            json=body,
            headers={
                "Content-Type": "application/json",
                "X-Goog-Api-Key": settings.google_maps_api_key,
                "X-Goog-FieldMask": "routes.duration,routes.distanceMeters,routes.polyline.encodedPolyline",
            },
            timeout=10.0,
        )
        response.raise_for_status()
        data = response.json()
    except httpx.HTTPError as exc:
        raise RouteLookupError(f"Routes API request failed: {exc}") from exc

    routes = data.get("routes")
    if not routes:
        raise RouteLookupError("No route found between the given points")

    route = routes[0]
    encoded_polyline = route["polyline"]["encodedPolyline"]
    duration_seconds = int(route["duration"].rstrip("s"))

    return {
        "distance_meters": route["distanceMeters"],
        "duration_seconds": duration_seconds,
        "points": decode_polyline(encoded_polyline),
    }
