# UniRide Matching Evaluation Report

Generated: 2026-10-04 20:06 UTC

## Methodology & caveats

- Dataset: 40 synthetic ride requests (`scripts/seed_test_data.py`) across 5 real NYC-area destinations and 4 Stony Brook-area pickup anchors, with randomized jitter, departure-time clusters, and preference mixes. Not real user data.
- Matching ran directly against `matching_service.find_matches()` (read-only, no Match rows persisted) — the same code path the live API uses.
- **Simulated acceptance rate** treats a top-match `total_score >= 0.6` as "would accept." This is a synthetic stand-in for human judgment, not measured user behavior — no real accept/reject data exists yet to calibrate or validate this threshold.
- "Avg time difference" is the raw schedule gap between two riders' departure times. It is **not** the architecture doc's "detour minutes" (the added driving time from detouring to pick someone up) — that would need a waypoint-routed Directions call per candidate pair, which Phase 6 deliberately deferred to keep external API usage bounded (see `app/matching/route_overlap.py`).
- Product/impact metrics (estimated trip savings, confirmed-ride count, repeat use, cancellation rate) are **not reported** — they require real usage over time, not a synthetic one-shot snapshot. Fabricating them here would violate the architecture doc's own section 18 caution against claiming savings before they're measured.

## Matching metrics (section 18)

| Metric | Value |
|---|---|
| Requests evaluated | 40 |
| % with ≥1 feasible match | 57.5% |
| Avg route overlap (top match) | 72.4% |
| Avg pickup distance (top match) | 1246m |
| Avg schedule time difference (top match) | 10.3 min |
| Simulated acceptance rate (threshold 0.6) | 73.9% |

## System metrics

| Metric | Value |
|---|---|
| Avg matching latency (service-layer, incl. DB queries) | 18.9 ms |
| p95 matching latency | 65.7 ms |

## Top 5 example matches

| Route | Matched with | Total score | Route overlap | Pickup dist. | Time diff. |
|---|---|---|---|---|---|
| Stony Brook Train Station → LaGuardia Airport | → LaGuardia Airport | 0.89 | 100% | 931m | 2min |
| Stony Brook Village Apartments → Times Square, Manhattan | → Times Square, Manhattan | 0.88 | 99% | 1002m | 2min |
| West Campus Residence Halls → Times Square, Manhattan | → Penn Station, Manhattan | 0.84 | 99% | 513m | 1min |
| Stony Brook University → Penn Station, Manhattan | → Times Square, Manhattan | 0.78 | 84% | 1461m | 5min |
| Stony Brook Train Station → Smith Haven Mall | → Smith Haven Mall | 0.78 | 50% | 658m | 9min |
