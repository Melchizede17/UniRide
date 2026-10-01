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

## Project status

Currently at Milestone 1 (Phase 0/1 of the architecture doc): project skeleton and
frontend/backend/database connectivity. Matching engine, auth, and real-time features
are implemented in later phases — see section 20 of the architecture doc.
