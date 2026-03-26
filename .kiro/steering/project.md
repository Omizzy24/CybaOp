# CybaOp — Project Context

## What This Is
CybaOp is an analytics intelligence platform for SoundCloud creators. It connects to a user's SoundCloud account via OAuth, fetches their profile and track data, runs it through an AI-powered analytics pipeline (LangGraph), and surfaces engagement metrics, trend detection, and actionable insights.

## Architecture
- Frontend: Next.js 15 (App Router) on Vercel — `cyba-op.vercel.app`
- Backend: FastAPI (Python 3.11) on Railway — `delightful-beauty-production-7537.up.railway.app`
- Database: Neon Postgres (serverless)
- Agent Pipeline: LangGraph with Google Gemini (not yet wired to frontend)
- Auth: SoundCloud OAuth → backend token exchange → JWT → httpOnly cookie

## Key Boundaries
- Frontend is a thin transport layer. It reads cookies and proxies to the backend. It never decodes JWTs, never calls SoundCloud directly (except the OAuth initiation redirect).
- Backend owns all business logic: token exchange, JWT signing/verification, user persistence, SoundCloud API calls, analytics pipeline.
- One token type: `cybaop_token` (JWT). No fallback auth paths.

## Tech Stack Details
- Python: 3.11, asyncpg (no ORM), Pydantic v2, structlog, httpx
- Node: 22 (local dev requires `/opt/homebrew/opt/node@22/bin`)
- Tailwind CSS v4 with custom theme vars in globals.css
- Tests: pytest with asyncio mode, run with `PYTHONPATH=backend python3.11 -m pytest backend/tests/unit/ -v`

## Environment
- Local dev: macOS, Node 22, Python 3.11
- `.env.local` has real SoundCloud creds (gitignored)
- `backend/.env` has placeholders (gitignored), use `.env.example` as template
- Branch: `feature/backend-api`

## Current State
- OAuth flow: frontend → backend delegation working, needs live end-to-end test
- Database: Neon Postgres connected, schema auto-initializes on startup
- Analytics pipeline: LangGraph graph defined but not wired to API yet
- UI: Landing page + dashboard + analytics skeleton deployed on Vercel

## Conventions
- Backend errors use custom exception hierarchy in `src/shared/errors.py`
- All API responses follow `AnalyticsResponse` / `ErrorResponse` models
- Structured logging via structlog (not print statements)
- Frontend fetch calls go through `lib/fetch.ts` (retry + timeout + backoff)
- No duplicate logic across frontend/backend — if the backend does it, the frontend doesn't
