# Initial engineering weights from section 5.4 of the architecture doc, not
# learned values. Revisit once match-acceptance data exists (section 17,
# Version 3 - ML Ranking).
WEIGHT_DESTINATION = 0.35
WEIGHT_TIME = 0.25
WEIGHT_PICKUP = 0.20
WEIGHT_PREFERENCE = 0.20


def compute_total_score(
    destination_score: float,
    time_score: float,
    pickup_score: float,
    preference_score: float,
) -> float:
    return (
        WEIGHT_DESTINATION * destination_score
        + WEIGHT_TIME * time_score
        + WEIGHT_PICKUP * pickup_score
        + WEIGHT_PREFERENCE * preference_score
    )
