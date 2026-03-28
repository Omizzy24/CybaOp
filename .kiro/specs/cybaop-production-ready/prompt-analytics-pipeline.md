# Analytics Pipeline Implementation Prompt

You are a senior systems engineer executing Requirements 4, 5, and 6 from the CybaOp production spec.

## CONTEXT

CybaOp is a working SaaS app. OAuth is live. Users can log in and see their SoundCloud profile on the dashboard. The next step is wiring the analytics pipeline so "View Analytics" shows real computed metrics.

### What exists and works:
- Frontend: Next.js 15 on Vercel at `cyba-op.vercel.app`
- Backend: FastAPI on Railway at `delightful-beauty-production-7537.up.railway.app`
- Database: Neon Postgres (users table has `soundcloud_token` per user)
- Auth: SoundCloud OAuth → JWT in `cybaop_token` cookie → backend verifies via `get_current_user`
- LangGraph pipeline defined at `backend/src/agent/graph.py` with nodes: fetch_profile, fetch_tracks, calculate_metrics, detect_trends, generate_insights, format_report
- Analytics route exists at `backend/src/api/routes/analytics.py` but returns mock/empty data
- Frontend analytics page exists at `app/dashboard/analytics/page.tsx` as a skeleton
- Backend fetch utility at `lib/fetch.ts` handles retry + timeout

### What needs to happen (3 tasks):

## TASK 1: Wire Analytics Pipeline to Backend Endpoint (Requirement 4)

File: `backend/src/api/routes/analytics.py`

1. The existing `GET /analytics/insights` endpoint must:
   - Extract user from JWT via `Depends(get_current_user)`
   - Fetch the user's `soundcloud_token` from DB via `get_user_token(user_id)`
   - IF token not found → return HTTP 401 `{ "success": false, "message": "SoundCloud token not found — re-authenticate" }`
   - Invoke the LangGraph pipeline with the SC token
   - For `free` tier: run fetch_profile + fetch_tracks + calculate_metrics + format_report (skip generate_insights which needs Gemini API key)
   - Return `AnalyticsResponse` with `success=true` and the report
   - IF pipeline throws → return `AnalyticsResponse` with `success=false` and error message (NOT a raw 500)

2. Read `backend/src/agent/graph.py` and `backend/src/agent/state.py` FIRST to understand the pipeline's input/output contract before wiring it.

3. The pipeline expects a state dict. Check what fields it needs (likely `token`, `tier`, `user_id`).

### Response Schema (MUST match exactly):
```json
{
  "request_id": "string",
  "success": true,
  "message": "Analytics generated successfully",
  "report": {
    "user_id": "string",
    "profile": ProfileData,
    "track_count": number,
    "top_tracks": TrackMetrics[],
    "metrics": AnalyticsMetrics | null,
    "trends": TrendAnalysis | null,
    "insights": InsightItem[],
    "tier": "free",
    "processing_time_ms": number,
    "nodes_executed": string[]
  },
  "processing_time_ms": number
}
```

## TASK 2: Create Frontend Analytics Proxy (Requirement 5)

File: `app/api/analytics/route.ts` (NEW FILE)

1. Extract `cybaop_token` from cookie
2. IF missing → return 401
3. Forward as `Authorization: Bearer {token}` to backend `GET /analytics/insights`
4. Use `backendFetch` from `@/lib/fetch` with `timeoutMs: 15_000`, `retries: 1`
5. Forward backend response status + JSON body unchanged
6. IF backend unreachable → return 502

## TASK 3: Update Analytics Page to Render Real Data (Requirement 6)

File: `app/dashboard/analytics/page.tsx`

1. On load, call `/api/analytics` (the proxy from Task 2)
2. Show loading skeleton while waiting
3. On success with `metrics` field → render: total_plays, total_likes, total_comments, avg_engagement_rate
4. Show top_tracks table: title, play_count, engagement_rate, performance_score
5. On success with `metrics: null` (free tier) → show profile + track count only, message "Upgrade to Pro for detailed metrics"
6. On error → show error message + retry button
7. On 401 → redirect to home page

## CONSTRAINTS

- DO NOT modify the auth flow (it works, don't touch it)
- DO NOT modify `backend/src/agent/graph.py` or any node files unless absolutely necessary
- DO NOT add new dependencies
- Read existing files BEFORE writing — understand the pipeline's state contract
- All backend errors must return structured JSON, never raw 500s
- Test the backend endpoint directly with curl after implementation
- Commit and push to `main` branch (NOT feature branch) so Vercel deploys to production

## VERIFICATION

After implementation, run these:

```bash
# Backend health
curl -s https://delightful-beauty-production-7537.up.railway.app/health

# Analytics without auth (expect 401)
curl -s -w "\n%{http_code}" https://delightful-beauty-production-7537.up.railway.app/analytics/insights

# Frontend proxy without auth (expect 401)
curl -s -w "\n%{http_code}" https://cyba-op.vercel.app/api/analytics
```

## KNOWN TRUTHS
- `NEXT_PUBLIC_*` vars are build-time only — use `req.headers.get("host")` for URLs
- Railway has cold starts — first request after idle is slow
- SoundCloud field names: `playback_count`, `favoritings_count`, `public_favorites_count`
- Neon connection strings need query params stripped for asyncpg
- Push to `main` for production deploy, NOT `feature/backend-api`

## STOP CONDITIONS
- If the pipeline state contract is unclear after reading graph.py → STOP and ask
- If generate_insights requires a Gemini API key that isn't set → skip it for free tier, don't crash
- If any file doesn't exist where expected → STOP and ask
