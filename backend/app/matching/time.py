def score(time_diff_minutes: float, allowed_window_minutes: float) -> float:
    if allowed_window_minutes <= 0:
        return 1.0 if time_diff_minutes == 0 else 0.0
    return max(0.0, 1.0 - (time_diff_minutes / allowed_window_minutes))
