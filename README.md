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

## Project status

Phases 1-6 of the architecture doc are done end-to-end. Creating a ride fetches
its real driving route from the Google Routes API and stores the geometry;
"Find Matches" runs a PostGIS eligibility pipeline (time/pickup/preference)
and scores candidates by real route overlap (buffer + intersection on the
stored route geometries) plus time/pickup/preference compatibility, then
Accept/Decline drives mutual acceptance through to a confirmed match. Falls
back to distance-based destination scoring if a route lookup ever fails.
The create-ride form still takes manual lat/lon (no map picker/autocomplete
yet — that's a separate Places API integration). Real-time match
notifications are Phase 7 — see section 20 of the architecture doc for the
full roadmap.
