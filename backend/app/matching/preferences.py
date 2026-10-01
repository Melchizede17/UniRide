from app.models.user import GenderPreference


def is_mutually_eligible(
    gender_a: str | None,
    preference_a: GenderPreference,
    gender_b: str | None,
    preference_b: GenderPreference,
) -> bool:
    requires_match = (
        preference_a == GenderPreference.REQUIRE_SAME_GENDER
        or preference_b == GenderPreference.REQUIRE_SAME_GENDER
    )
    if not requires_match:
        return True
    return gender_a is not None and gender_b is not None and gender_a == gender_b


def score(
    gender_a: str | None,
    preference_a: GenderPreference,
    gender_b: str | None,
    preference_b: GenderPreference,
) -> float:
    if gender_a is None or gender_b is None:
        return 0.5

    wants_same_gender = (
        preference_a != GenderPreference.NO_PREFERENCE or preference_b != GenderPreference.NO_PREFERENCE
    )
    if not wants_same_gender:
        return 1.0
    return 1.0 if gender_a == gender_b else 0.5
