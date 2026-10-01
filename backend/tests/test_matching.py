import pytest

from app.matching import destination, eligibility, pickup, preferences, time as time_scoring
from app.matching.scorer import compute_total_score
from app.models.user import GenderPreference


@pytest.mark.parametrize(
    "score_fn",
    [time_scoring.score, pickup.score, destination.score],
)
def test_linear_decay_scores_bounded(score_fn) -> None:
    assert score_fn(0, 100) == 1.0
    assert score_fn(100, 100) == 0.0
    assert score_fn(50, 100) == pytest.approx(0.5)
    assert score_fn(150, 100) == 0.0  # never goes negative
    assert score_fn(0, 0) == 1.0  # exact match with zero tolerance is still a match


def test_time_score_zero_window_rejects_any_difference() -> None:
    assert time_scoring.score(5, 0) == 0.0


def test_eligibility_thresholds() -> None:
    assert eligibility.is_time_compatible(20, 20) is True
    assert eligibility.is_time_compatible(21, 20) is False
    assert eligibility.is_pickup_feasible(2000, 2000) is True
    assert eligibility.is_pickup_feasible(2001, 2000) is False
    assert eligibility.is_destination_feasible(5000, 5000) is True
    assert eligibility.is_destination_feasible(5001, 5000) is False


def test_preference_require_same_gender_blocks_mismatch() -> None:
    assert (
        preferences.is_mutually_eligible(
            "female", GenderPreference.REQUIRE_SAME_GENDER, "male", GenderPreference.NO_PREFERENCE
        )
        is False
    )
    assert (
        preferences.is_mutually_eligible(
            "female", GenderPreference.REQUIRE_SAME_GENDER, "female", GenderPreference.NO_PREFERENCE
        )
        is True
    )


def test_preference_require_same_gender_blocks_unknown_gender() -> None:
    assert (
        preferences.is_mutually_eligible(
            None, GenderPreference.REQUIRE_SAME_GENDER, "female", GenderPreference.NO_PREFERENCE
        )
        is False
    )


def test_preference_no_preference_never_blocks() -> None:
    assert (
        preferences.is_mutually_eligible(
            "male", GenderPreference.NO_PREFERENCE, "female", GenderPreference.NO_PREFERENCE
        )
        is True
    )


def test_preference_score_unknown_gender_is_neutral() -> None:
    assert preferences.score(None, GenderPreference.NO_PREFERENCE, "female", GenderPreference.NO_PREFERENCE) == 0.5


def test_preference_score_no_preference_is_full() -> None:
    assert preferences.score("male", GenderPreference.NO_PREFERENCE, "female", GenderPreference.NO_PREFERENCE) == 1.0


def test_preference_score_prefer_same_gender_rewards_match() -> None:
    assert (
        preferences.score(
            "female", GenderPreference.PREFER_SAME_GENDER, "female", GenderPreference.NO_PREFERENCE
        )
        == 1.0
    )
    assert (
        preferences.score(
            "female", GenderPreference.PREFER_SAME_GENDER, "male", GenderPreference.NO_PREFERENCE
        )
        == 0.5
    )


def test_compute_total_score_weights_sum_to_one_at_max() -> None:
    assert compute_total_score(1.0, 1.0, 1.0, 1.0) == pytest.approx(1.0)
    assert compute_total_score(0.0, 0.0, 0.0, 0.0) == 0.0
