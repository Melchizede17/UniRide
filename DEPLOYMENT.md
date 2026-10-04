# Deploying UniRide

Stack: **Vercel** (frontend) + **Render** (backend) + **Supabase** (Postgres + PostGIS).
All three have free tiers suitable for a portfolio deployment. GitHub repo:
https://github.com/Melchizede17/UniRide

This doc covers the steps that need your own account/login — I can't create
accounts or handle billing on your behalf. Everything else (render.yaml,
CI, production-readiness fixes) is already in the repo.

## 1. Database: Supabase

1. Create a project at [supabase.com](https://supabase.com) (free tier).
2. In the SQL Editor, run: `CREATE EXTENSION IF NOT EXISTS postgis;`
3. Go to **Project Settings → Database** and copy the connection string.
   Use the **Transaction pooler** string (port 6543), not the direct
   connection (port 5432) — several hosts (including Render's free tier)
   don't support the IPv6 required for Supabase's direct connection, and the
   pooler avoids that entirely. Our app doesn't need session-level pooling
   features, so transaction-mode pooling is fine.
4. Adjust the connection string for SQLAlchemy + psycopg3:
   - Supabase gives you: `postgresql://postgres.xxxx:[PASSWORD]@aws-...pooler.supabase.com:6543/postgres`
   - You need: `postgresql+psycopg://postgres.xxxx:[PASSWORD]@aws-...pooler.supabase.com:6543/postgres`
   - (just add `+psycopg` after `postgresql`)
5. Run migrations against it once (from your machine, with this as `DATABASE_URL`):
   ```bash
   cd /Users/UniRide
   DATABASE_URL="postgresql+psycopg://...(from step 4)..." \
     backend/.venv/bin/python -m alembic -c alembic.ini upgrade head
   ```
   Tell me when you've got the connection string if you'd rather I run this
   step — I'll need the string, handled the same way as the Google Maps key
   (never pasted into a committed file).

## 2. Backend: Render

1. Create an account at [render.com](https://render.com), connect your GitHub account.
2. **New → Blueprint**, select the `Melchizede17/UniRide` repo. Render reads
   `render.yaml` from the repo root automatically.
3. Before the first deploy, set these environment variables in the Render
   dashboard (Dashboard → uniride-backend → Environment):
   - `DATABASE_URL` — the Supabase pooler connection string from step 1.4
   - `SECRET_KEY` — generate with:
     ```bash
     python -c "import secrets; print(secrets.token_urlsafe(32))"
     ```
   - `GOOGLE_MAPS_API_KEY` — your existing key (needs the Routes API enabled,
     same as local dev — see `backend/.env.example`)
   - `CORS_ORIGINS` — temporarily `["http://localhost:5173"]`; you'll update
     this in step 3 once you have the Vercel URL.
4. Deploy. `render.yaml` already points `startCommand` at running migrations
   before starting uvicorn, so the schema applies automatically on deploy.
5. Once live, your backend URL is `https://uniride-backend.onrender.com`
   (or whatever Render assigns). Confirm it works:
   ```bash
   curl https://uniride-backend.onrender.com/api/v1/health
   ```

**Free tier note:** Render's free web services spin down after ~15 minutes
of inactivity. The first request after that takes 30-60s to cold-start —
expected, not a bug, for a demo link.

## 3. Frontend: Vercel

1. Create an account at [vercel.com](https://vercel.com), connect GitHub.
2. **Add New → Project**, select the `UniRide` repo.
3. Set **Root Directory** to `frontend` (this is a monorepo).
4. Vercel auto-detects Vite; no build command changes needed.
5. Set the environment variable:
   - `VITE_API_BASE_URL` = `https://uniride-backend.onrender.com/api/v1`
     (your actual Render URL from step 2.5)
6. Deploy. Your frontend URL will be something like `uniride.vercel.app` or
   `uniride-<random>.vercel.app`.

## 4. Close the loop: update CORS

Back on Render, update `CORS_ORIGINS` to your real Vercel URL:
```
["https://uniride.vercel.app"]
```
Redeploy the backend (Render redeploys automatically on env var changes, or
trigger manually from the dashboard).

## 5. Verify

```bash
curl https://uniride-backend.onrender.com/api/v1/health
# {"status":"ok"}
```

Then open the Vercel URL in a browser and walk through: register → create a
ride → Find Matches → accept/reject. The WebSocket connection
(`wss://uniride-backend.onrender.com/api/v1/ws/matches`) should work
automatically since `getWebSocketUrl()` derives it from `VITE_API_BASE_URL`.

## Logging & monitoring

- Render's dashboard has a built-in log viewer (Logs tab) and basic
  CPU/memory metrics — sufficient for this scale, no extra setup needed.
- Vercel similarly shows build/runtime logs and basic analytics.
- Nothing like Sentry/Datadog is wired up — not needed yet at this scale,
  and I won't set up a third-party monitoring account without being asked.

## What's NOT automated

- Pushing to `main` does **not** automatically redeploy — that requires
  connecting the Render/Vercel dashboards to the GitHub repo (steps 2.2 and
  3.2 above), which is a one-time setup you do in each platform's UI. Once
  connected, both platforms redeploy on every push to `main` natively; no
  GitHub Actions deploy step is needed for that part. `.github/workflows/ci.yml`
  only runs tests, not deployment.
