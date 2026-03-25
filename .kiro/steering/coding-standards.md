---
inclusion: auto
---

# Coding Standards

## Python (Backend)
- Type hints on all function signatures
- Async by default for I/O operations
- Use `httpx.AsyncClient` for HTTP calls, never `requests`
- Pydantic models for all data contracts — no raw dicts crossing API boundaries
- Structured logging: `logger.info("event_name", key=value)` not `logger.info(f"...")`
- Error handling: raise domain-specific exceptions from `src/shared/errors.py`, never bare `Exception`
- Imports: stdlib → third-party → local, separated by blank lines
- No wildcard imports

## TypeScript (Frontend)
- All backend calls go through `lib/fetch.ts` — never raw `fetch()` in route handlers
- Server components by default, `"use client"` only when needed
- No inline styles — use Tailwind classes
- API routes are thin proxies — no business logic in Next.js
- Type interfaces for all API response shapes

## Both
- No TODO comments in committed code — track in issues
- No console.log in production paths — use structured logging (backend) or remove (frontend)
- Environment variables: never hardcode secrets, always use env vars with sensible defaults
- Test before commit: `PYTHONPATH=backend python3.11 -m pytest backend/tests/unit/ -x -q`
