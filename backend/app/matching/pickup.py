def score(distance_meters: float, max_distance_meters: float) -> float:
    if max_distance_meters <= 0:
        return 1.0 if distance_meters == 0 else 0.0
    return max(0.0, 1.0 - (distance_meters / max_distance_meters))
