import pytest

from app.matching import route_overlap
from app.services.maps_service import decode_polyline


def test_decode_polyline_matches_google_reference_vector() -> None:
    # Official example from Google's Encoded Polyline Algorithm Format docs.
    result = decode_polyline("_p~iF~ps|U_ulLnnqC_mqNvxq`@")
    expected = [(38.5, -120.2), (40.7, -120.95), (43.252, -126.453)]
    assert len(result) == len(expected)
    for (lat, lng), (exp_lat, exp_lng) in zip(result, expected):
        assert lat == pytest.approx(exp_lat, abs=1e-5)
        assert lng == pytest.approx(exp_lng, abs=1e-5)


def test_route_overlap_score_full_overlap_no_detour() -> None:
    assert route_overlap.score(1.0, 0.0, 0.0) == pytest.approx(1.0)


def test_route_overlap_score_no_overlap_max_detour() -> None:
    assert route_overlap.score(0.0, 1.0, 1.0) == 0.0


def test_route_overlap_score_weights_overlap_most_heavily() -> None:
    high_overlap_no_detour = route_overlap.score(1.0, 0.0, 0.0)
    low_overlap_no_detour = route_overlap.score(0.2, 0.0, 0.0)
    assert high_overlap_no_detour > low_overlap_no_detour
    # overlap alone (weight 0.5) outweighs a single fully-penalized detour term (weight 0.25)
    assert route_overlap.score(1.0, 1.0, 0.0) > route_overlap.score(0.0, 0.0, 0.0)


def test_route_overlap_score_clamps_out_of_range_inputs() -> None:
    assert route_overlap.score(1.5, -0.5, 2.0) == route_overlap.score(1.0, 0.0, 1.0)
