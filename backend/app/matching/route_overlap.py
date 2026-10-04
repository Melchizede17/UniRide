# Phase 6: real route-overlap scoring, replacing the Phase 5 distance-based
# destination stand-in. R = alpha*O + beta*(1-time_detour) + gamma*(1-distance_detour),
# per section 6.2 of the architecture doc.
#
# time_detour/distance_detour here are V1 approximations derived from values
# already computed during eligibility (time difference, pickup distance)
# rather than a second waypoint-routed Directions call per candidate pair --
# a true "how much longer does MY trip take if I detour to pick up the other
# rider" number would need that extra API call per pair. Revisit if request
# volume/cost allow it later.

ALPHA_OVERLAP = 0.5
BETA_TIME_DETOUR = 0.25
GAMMA_DISTANCE_DETOUR = 0.25


def score(overlap_fraction: float, time_detour: float, distance_detour: float) -> float:
    overlap_fraction = max(0.0, min(1.0, overlap_fraction))
    time_detour = max(0.0, min(1.0, time_detour))
    distance_detour = max(0.0, min(1.0, distance_detour))
    return (
        ALPHA_OVERLAP * overlap_fraction
        + BETA_TIME_DETOUR * (1 - time_detour)
        + GAMMA_DISTANCE_DETOUR * (1 - distance_detour)
    )
