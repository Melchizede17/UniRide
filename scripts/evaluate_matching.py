"""Evaluates matching quality against a synthetic dataset (architecture doc
Phase 8 / section 18's Matching Metrics). Read-only with respect to Match
rows - calls matching_service.find_matches() directly, never persists
suggestions, so running this repeatedly never creates duplicate/stale Match
rows.

By default: seeds the synthetic dataset, measures it, writes the report,
then removes the synthetic data again - so it never lingers in the same dev
DB the pytest suite runs against. Pass --keep-data to leave it in place
afterward for manual exploration.

Usage:
    python scripts/evaluate_matching.py
    python scripts/evaluate_matching.py --keep-data
    python scripts/evaluate_matching.py --threshold 0.7
"""

import math
import statistics
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from geoalchemy2.shape import to_shape  # noqa: E402

from app.core.database import SessionLocal  # noqa: E402
from app.models import RideRequest  # noqa: E402
from app.services import matching_service  # noqa: E402
from seed_test_data import clear_synthetic_data, seed_dataset  # noqa: E402

DEFAULT_ACCEPTANCE_THRESHOLD = 0.6
OUTPUT_PATH = Path(__file__).resolve().parents[1] / "output" / "matching_evaluation_report.md"

EARTH_RADIUS_METERS = 6_371_000


def haversine_meters(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lambda = math.radians(lng2 - lng1)
    a = math.sin(d_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2) ** 2
    return 2 * EARTH_RADIUS_METERS * math.asin(math.sqrt(a))


def evaluate(rides: list[RideRequest], db, threshold: float) -> dict:
    per_request = []
    latencies_seconds = []

    for ride in rides:
        start = time.perf_counter()
        candidates = matching_service.find_matches(db, ride)
        latencies_seconds.append(time.perf_counter() - start)

        has_match = len(candidates) > 0
        top = candidates[0] if has_match else None

        entry = {
            "ride_id": str(ride.id),
            "pickup_address": ride.pickup_address,
            "destination_address": ride.destination_address,
            "num_candidates": len(candidates),
            "has_match": has_match,
        }

        if top is not None:
            pickup_shape = to_shape(ride.pickup_point)
            other_pickup_shape = to_shape(top.ride_request.pickup_point)
            pickup_distance_m = haversine_meters(
                pickup_shape.y, pickup_shape.x, other_pickup_shape.y, other_pickup_shape.x
            )
            time_diff_minutes = abs((ride.departure_time - top.ride_request.departure_time).total_seconds()) / 60

            entry.update(
                {
                    "top_total_score": top.total_score,
                    "top_route_overlap": top.route_overlap_score,
                    "top_pickup_distance_m": pickup_distance_m,
                    "top_time_diff_minutes": time_diff_minutes,
                    "would_accept": top.total_score >= threshold,
                    "other_destination": top.ride_request.destination_address,
                    "pair_key": frozenset((str(ride.id), str(top.ride_request.id))),
                }
            )
        per_request.append(entry)

    with_match = [e for e in per_request if e["has_match"]]
    pct_with_match = 100 * len(with_match) / len(per_request) if per_request else 0.0
    simulated_acceptance_rate = (
        100 * sum(1 for e in with_match if e["would_accept"]) / len(with_match) if with_match else 0.0
    )

    return {
        "per_request": per_request,
        "total_requests": len(per_request),
        "pct_with_at_least_one_match": pct_with_match,
        "avg_route_overlap": statistics.mean(e["top_route_overlap"] for e in with_match) if with_match else None,
        "avg_pickup_distance_m": statistics.mean(e["top_pickup_distance_m"] for e in with_match) if with_match else None,
        "avg_time_diff_minutes": statistics.mean(e["top_time_diff_minutes"] for e in with_match) if with_match else None,
        "simulated_acceptance_rate_pct": simulated_acceptance_rate,
        "acceptance_threshold": threshold,
        "avg_matching_latency_ms": statistics.mean(latencies_seconds) * 1000,
        "p95_matching_latency_ms": (
            statistics.quantiles(latencies_seconds, n=20)[18] * 1000 if len(latencies_seconds) >= 20 else max(latencies_seconds) * 1000
        ),
    }


def render_report(results: dict) -> str:
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    with_match = [e for e in results["per_request"] if e["has_match"]]
    ranked = sorted(with_match, key=lambda e: e["top_total_score"], reverse=True)

    top_examples = []
    seen_pairs = set()
    for entry in ranked:
        if entry["pair_key"] in seen_pairs:
            continue
        seen_pairs.add(entry["pair_key"])
        top_examples.append(entry)
        if len(top_examples) == 5:
            break

    lines = [
        "# UniRide Matching Evaluation Report",
        "",
        f"Generated: {timestamp}",
        "",
        "## Methodology & caveats",
        "",
        f"- Dataset: {results['total_requests']} synthetic ride requests "
        "(`scripts/seed_test_data.py`) across 5 real NYC-area destinations and 4 "
        "Stony Brook-area pickup anchors, with randomized jitter, departure-time "
        "clusters, and preference mixes. Not real user data.",
        "- Matching ran directly against `matching_service.find_matches()` "
        "(read-only, no Match rows persisted) — the same code path the live API uses.",
        f"- **Simulated acceptance rate** treats a top-match `total_score >= "
        f"{results['acceptance_threshold']}` as \"would accept.\" This is a synthetic "
        "stand-in for human judgment, not measured user behavior — no real "
        "accept/reject data exists yet to calibrate or validate this threshold.",
        "- \"Avg time difference\" is the raw schedule gap between two riders' "
        "departure times. It is **not** the architecture doc's \"detour minutes\" "
        "(the added driving time from detouring to pick someone up) — that would "
        "need a waypoint-routed Directions call per candidate pair, which Phase 6 "
        "deliberately deferred to keep external API usage bounded (see "
        "`app/matching/route_overlap.py`).",
        "- Product/impact metrics (estimated trip savings, confirmed-ride count, "
        "repeat use, cancellation rate) are **not reported** — they require real "
        "usage over time, not a synthetic one-shot snapshot. Fabricating them here "
        "would violate the architecture doc's own section 18 caution against "
        "claiming savings before they're measured.",
        "",
        "## Matching metrics (section 18)",
        "",
        "| Metric | Value |",
        "|---|---|",
        f"| Requests evaluated | {results['total_requests']} |",
        f"| % with ≥1 feasible match | {results['pct_with_at_least_one_match']:.1f}% |",
        f"| Avg route overlap (top match) | {_fmt_pct(results['avg_route_overlap'])} |",
        f"| Avg pickup distance (top match) | {_fmt_meters(results['avg_pickup_distance_m'])} |",
        f"| Avg schedule time difference (top match) | {_fmt_minutes(results['avg_time_diff_minutes'])} |",
        f"| Simulated acceptance rate (threshold {results['acceptance_threshold']}) | "
        f"{results['simulated_acceptance_rate_pct']:.1f}% |",
        "",
        "## System metrics",
        "",
        "| Metric | Value |",
        "|---|---|",
        f"| Avg matching latency (service-layer, incl. DB queries) | {results['avg_matching_latency_ms']:.1f} ms |",
        f"| p95 matching latency | {results['p95_matching_latency_ms']:.1f} ms |",
        "",
        "## Top 5 example matches",
        "",
        "| Route | Matched with | Total score | Route overlap | Pickup dist. | Time diff. |",
        "|---|---|---|---|---|---|",
    ]

    for e in top_examples:
        lines.append(
            f"| {e['pickup_address']} → {e['destination_address']} "
            f"| → {e['other_destination']} "
            f"| {e['top_total_score']:.2f} "
            f"| {e['top_route_overlap']:.0%} "
            f"| {e['top_pickup_distance_m']:.0f}m "
            f"| {e['top_time_diff_minutes']:.0f}min |"
        )

    lines.append("")
    return "\n".join(lines)


def _fmt_pct(value: float | None) -> str:
    return f"{value:.1%}" if value is not None else "n/a (no matches found)"


def _fmt_meters(value: float | None) -> str:
    return f"{value:.0f}m" if value is not None else "n/a (no matches found)"


def _fmt_minutes(value: float | None) -> str:
    return f"{value:.1f} min" if value is not None else "n/a (no matches found)"


def main() -> None:
    keep_data = "--keep-data" in sys.argv
    threshold = DEFAULT_ACCEPTANCE_THRESHOLD
    if "--threshold" in sys.argv:
        threshold = float(sys.argv[sys.argv.index("--threshold") + 1])

    db = SessionLocal()
    try:
        print("Seeding synthetic dataset...")
        rides = seed_dataset(db, verbose=False)
        print(f"Seeded {len(rides)} requests. Running matching evaluation...")

        results = evaluate(rides, db, threshold)
        report = render_report(results)

        OUTPUT_PATH.parent.mkdir(exist_ok=True)
        OUTPUT_PATH.write_text(report)
        print(f"\nReport written to {OUTPUT_PATH}")
        print(f"\n{results['pct_with_at_least_one_match']:.1f}% of requests had >=1 feasible match")
        print(f"Simulated acceptance rate: {results['simulated_acceptance_rate_pct']:.1f}%")

        if keep_data:
            print("\n--keep-data passed: synthetic dataset left in place.")
        else:
            removed = clear_synthetic_data(db)
            print(f"\nCleaned up {removed} synthetic users.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
