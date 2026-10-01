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

Phase 4 of the architecture doc is done: a working frontend (login, register,
dashboard, create-ride form, ride history) on top of the Phase 2/3 backend
(SQLAlchemy models + Alembic migrations, JWT auth, full ride CRUD). The
create-ride form takes manual lat/lon for now — map autocomplete needs a
Google Maps API key, which isn't configured yet (only `GOOGLE_MAPS_API_KEY`
config wiring exists so far — no `maps_service` implementation). The
matching engine, route overlap, and real-time features
are implemented in later phases — see section 20 of the architecture doc.
