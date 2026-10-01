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

Phase 5 of the architecture doc is done: a working matching engine v1 on top
of Phases 1-4 (frontend, JWT auth, ride CRUD, SQLAlchemy models). Given an
active ride request, `GET /rides/{id}/matches` runs a PostGIS-backed
eligibility + weighted-scoring pipeline (destination distance, time overlap,
pickup proximity, gender preference) and returns ranked `SUGGESTED` matches;
`POST /matches/{id}/accept` and `/reject` drive mutual acceptance through to
a `CONFIRMED` match. Destination scoring is distance-based for now — true
route-overlap scoring (and the frontend match-results page) land in Phase 6.
The create-ride form still takes manual lat/lon since Maps isn't configured
yet (only `GOOGLE_MAPS_API_KEY` config wiring exists — no `maps_service`
implementation). Real-time match notifications are Phase 7 — see section 20
of the architecture doc for the full roadmap.
