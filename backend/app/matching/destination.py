# Phase 5: destination similarity is distance-based (section 6.1 of the
# architecture doc). True route-overlap scoring (section 6.2) lands in Phase 6
# and will replace/augment this.


def score(distance_meters: float, max_distance_meters: float) -> float:
    if max_distance_meters <= 0:
        return 1.0 if distance_meters == 0 else 0.0
    return max(0.0, 1.0 - (distance_meters / max_distance_meters))
