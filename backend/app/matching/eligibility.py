# Mandatory (Stage A) constraints from section 5.4 of the architecture doc.
# ride_request.status == ACTIVE / candidate != current_user are enforced as
# SQL WHERE clauses in services/matching_service.py, not here.
# available_capacity >= required_capacity is not applicable: UniRide matches
# passengers to coordinate a shared ride, there's no vehicle/driver record
# with a seat count in this schema.


def is_time_compatible(time_diff_minutes: float, allowed_window_minutes: float) -> bool:
    return time_diff_minutes <= allowed_window_minutes


def is_pickup_feasible(distance_meters: float, max_distance_meters: float) -> bool:
    return distance_meters <= max_distance_meters


def is_destination_feasible(distance_meters: float, max_distance_meters: float) -> bool:
    return distance_meters <= max_distance_meters
