# UniRide

Full-stack intelligent student ride-matching platform. Helps university students find
compatible passengers for a shared ride so they can coordinate one trip and split
transportation costs. UniRide is a coordination/matching platform — not a ride-hailing
service and does not provide drivers.

See `UniRide_Complete_Project_Architecture.md` for the full architecture, data model,
matching algorithm design, and phased roadmap.

## Stack

- Backend: FastAPI (Python 3.12), SQLAlchemy, PostgreSQL + PostGIS
- Frontend: React + TypeScript (Vite)
- Local infra: Docker Compose (PostGIS)

## Getting started

### 1. Database

```bash
cp .env.example .env
docker compose up -d
```

### 2. Backend

```bash
cd backend
cp .env.example .env   # fill in GOOGLE_MAPS_API_KEY (needs Routes API enabled)
pyenv local 3.12.14   # already pinned via .python-version
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

API available at `http://localhost:8000`, docs at `http://localhost:8000/docs`.

### 3. Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend available at `http://localhost:5173`.

### 4. Database migrations

```bash
cd backend && source .venv/bin/activate
cd .. && alembic upgrade head
```

Alembic config lives at the repo root (`alembic.ini`), migrations under
`database/migrations/`, models under `backend/app/models/`.

### 5. Evaluate matching quality

```bash
cd backend && source .venv/bin/activate
cd .. && python scripts/evaluate_matching.py
```

Seeds a synthetic dataset, measures matching quality against section 18's
metrics, writes a report to `output/matching_evaluation_report.md`, then
cleans the synthetic data back up (pass `--keep-data` to leave it in place
for manual exploration instead).

## Project status

Phases 1-8 of the architecture doc are done end-to-end. Creating a ride fetches
its real driving route from the Google Routes API and stores the geometry;
"Find Matches" runs a PostGIS eligibility pipeline (time/pickup/preference)
and scores candidates by real route overlap (buffer + intersection on the
stored route geometries) plus time/pickup/preference compatibility. Matching
stays on-demand (click "Find Matches"), but the *notification* side is real-time:
finding a new match, accepting, confirming, and rejecting all push a live
WebSocket notification to the other rider (bell icon + toast + `/notifications`
inbox in the frontend), backed by `GET/PATCH /notifications`. Falls back to
distance-based destination scoring if a route lookup ever fails. `scripts/evaluate_matching.py`
measures matching quality against a synthetic dataset and writes a report to
`output/`. The create-ride form still takes manual lat/lon (no map
picker/autocomplete yet — that's a separate Places API integration) — see
section 20 of the architecture doc for the full roadmap.
