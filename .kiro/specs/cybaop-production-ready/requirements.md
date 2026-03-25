# Requirements Document

## Introduction

CybaOp is an analytics intelligence platform for SoundCloud creators. The system is currently in a POC state with several broken integration points that prevent real users from completing the login flow or accessing analytics. This spec covers the work required to take CybaOp from POC to a working production micro-SaaS: fixing the OAuth callback, removing the dual-token fallback path, wiring the LangGraph analytics pipeline to the frontend, and hardening the system for production traffic.

## System Flow

```
Browser
  → Vercel GET /api/auth/soundcloud (redirect to SoundCloud)
  → SoundCloud OAuth consent page
  → Vercel GET /api/auth/callback?code=XXX
    → Vercel POST https://api.soundcloud.com/oauth2/token (exchange code, <10s)
    → Railway POST /auth/token-from-sc { access_token } (register user, <8s)
    ← Set cybaop_token cookie (JWT)
    ← Redirect to /dashboard
  → Vercel GET /dashboard (client-side page)
    → Vercel GET /api/auth/me (proxy)
      → Railway GET /auth/me (JWT verified, profile returned)
  → Vercel GET /dashboard/analytics (client-side page)
    → Vercel GET /api/analytics (proxy)
      → Railway GET /analytics/insights (JWT verified, pipeline runs)
        → SoundCloud /me + /me/tracks (fetch data)
        → LangGraph pipeline (compute metrics)
      ← AnalyticsResponse
```

**Critical constraint:** THE Callback_Handler SHALL use the exact same `redirect_uri` string for both the authorization request AND the token exchange. Mismatch causes `invalid_grant`.

## Non-Goals

- No refresh token handling
- No background jobs or async task queues
- No caching layer (Redis/ElastiCache)
- No multi-provider OAuth (Spotify, etc.)
- No payment/billing integration
- No user settings page
- No email notifications

## Glossary

- **Callback_Handler**: Next.js API route at `app/api/auth/callback/route.ts`
- **SC_Token**: SoundCloud OAuth access token obtained by exchanging an authorization code
- **CybaOp_JWT**: Signed JWT issued by Backend; the only token stored in `cybaop_token` cookie
- **Backend**: FastAPI on Railway at `delightful-beauty-production-7537.up.railway.app`
- **Frontend**: Next.js 15 on Vercel at `cyba-op.vercel.app`
- **Analytics_Pipeline**: LangGraph StateGraph in `backend/src/agent/graph.py`
- **Analytics_Proxy**: Next.js API route at `app/api/analytics/route.ts`
- **Me_Proxy**: Next.js API route at `app/api/auth/me/route.ts`

## Known Truths (System Memory)

- `NEXT_PUBLIC_*` variables are build-time only in Next.js — they are `undefined` at runtime if not present during `next build`
- Railway free tier has cold starts (10-30s) that can kill SoundCloud auth codes (~30s expiry)
- SoundCloud API field names: `playback_count` (not `plays_count`), `favoritings_count` (not `likes_count`), `public_favorites_count` for profile likes
- Neon Postgres connection strings include `channel_binding=require` which asyncpg cannot handle — must strip query params
- SoundCloud OAuth codes are single-use — retrying with the same code always fails with `invalid_grant`
- `asyncpg` requires explicit SSL context for Neon connections

## Cookie Specification

| Property | Value |
|----------|-------|
| Name | `cybaop_token` |
| HttpOnly | `true` |
| Secure | `true` (production), `false` (localhost) |
| SameSite | `lax` |
| Path | `/` |
| Max-Age | 604800 (7 days) |

IF the cookie cannot be set (e.g., redirect fails before `Set-Cookie` is sent), the Callback_Handler SHALL treat this as a failure and redirect to `/?error=cookie_failed`.

## JWT Contract

| Property | Value |
|----------|-------|
| Algorithm | HS256 |
| Signed with | `JWT_SECRET` env var |
| Payload fields | `sub` (user_id), `username`, `tier`, `iat`, `exp` |
| Expiry | 7 days from issuance |

IF JWT is invalid or expired, Backend SHALL return HTTP 401 with `{ "message": "invalid_token" }`. This applies to ALL authenticated endpoints (`/auth/me`, `/analytics/insights`, `/auth/logout`).

## Host Header Handling

The Callback_Handler derives `baseUrl` from `req.headers.get("host")`.

IF `host` header is missing or null:
- Callback_Handler SHALL fallback to `process.env.VERCEL_URL` (auto-set by Vercel)
- IF both are missing, return HTTP 500 with `{ "error": "missing_host" }`

```typescript
const host = req.headers.get("host") || process.env.VERCEL_URL;
if (!host) return NextResponse.json({ error: "missing_host" }, { status: 500 });
const baseUrl = `https://${host}`;
```

## Cold Start Handling

IF Backend `/auth/token-from-sc` times out (>8s):
- Callback_Handler SHALL NOT retry (OAuth codes are single-use)
- SHALL redirect to `/?error=service_unavailable`
- SHALL NOT store a raw SC_Token as fallback

Rationale: SoundCloud codes expire in ~30s and are single-use. A retry with the same code always fails with `invalid_grant`. Railway cold starts on free tier take 10-30s, which can exceed the code's lifetime.

## Cross-Service Timeout Requirements

| Call | Max Time | On Timeout |
|------|----------|------------|
| Callback_Handler → SoundCloud token exchange | 10s | Redirect to `/?error=timeout` |
| Callback_Handler → Backend `/auth/token-from-sc` | 8s | Redirect to `/?error=service_unavailable` |
| Me_Proxy → Backend `/auth/me` | 10s | Return HTTP 502 `{ "error": "timeout" }` |
| Analytics_Proxy → Backend `/analytics/insights` | 15s | Return HTTP 504 `{ "error": "timeout" }` |

## API Response Schemas

### AuthTokenResponse (Backend → Frontend)
```json
{
  "access_token": "string (CybaOp JWT)",
  "token_type": "bearer",
  "user_id": "string",
  "username": "string",
  "tier": "free | pro | enterprise"
}
```

### Me Response (Backend → Frontend)
```json
{
  "user_id": "string",
  "username": "string",
  "display_name": "string",
  "followers_count": 0,
  "following_count": 0,
  "track_count": 0,
  "playlist_count": 0,
  "likes_count": 0,
  "avatar_url": "string",
  "profile_url": "string",
  "tier": "free"
}
```

### AnalyticsResponse (Backend → Frontend)
```json
{
  "request_id": "string",
  "success": true,
  "message": "string | null",
  "report": {
    "user_id": "string",
    "profile": { "username": "string", "followers_count": 0 },
    "track_count": 0,
    "top_tracks": [
      { "track_id": "string", "title": "string", "engagement_rate": 0.0, "performance_score": 0.0 }
    ],
    "metrics": {
      "total_plays": 0,
      "total_likes": 0,
      "total_comments": 0,
      "avg_engagement_rate": 0.0,
      "catalog_concentration": 0.0
    } | null,
    "trends": null,
    "insights": []
  } | null,
  "processing_time_ms": 0
}
```

### Error Response (all error paths)
```json
{
  "success": false,
  "message": "string",
  "error_code": "string | null"
}
```

## Idempotency Requirements

- Backend `POST /auth/token-from-sc` MUST be idempotent — same SoundCloud user MUST NOT create duplicate DB records (upsert by `soundcloud_user_id`)
- Backend `GET /analytics/insights` is naturally idempotent (read-only pipeline)

---

## Requirements


### Requirement 1: OAuth Callback Produces a Valid Redirect URL

**User Story:** As a SoundCloud creator, I want the OAuth callback to redirect me to the dashboard after login, so that I can access my analytics without seeing a broken URL error.

#### Acceptance Criteria

1. WHEN the Callback_Handler receives a request, THE Callback_Handler SHALL derive the base URL from the `host` request header as `https://${req.headers.get("host")}`, NOT from `NEXT_PUBLIC_BASE_URL`
2. WHEN the SoundCloud authorization code exchange succeeds, THE Callback_Handler SHALL redirect the user to `{base_url}/dashboard` with the `cybaop_token` cookie set
3. THE Callback_Handler SHALL use the exact same `redirect_uri` value for the token exchange as was used in the authorization request (value from `SOUNDCLOUD_REDIRECT_URI` env var)
4. IF the SoundCloud authorization code exchange fails, THEN THE Callback_Handler SHALL redirect to `{base_url}/?error=auth_failed`
5. IF an unhandled exception occurs, THEN THE Callback_Handler SHALL redirect to `{base_url}/?error=unexpected`
6. IF `host` header is missing, THE Callback_Handler SHALL fallback to `process.env.VERCEL_URL`; if both missing, return HTTP 500 with `{ "error": "missing_host" }`

#### Verification

```bash
# Test 1: Callback with fake code should redirect, NOT 500
curl -s -o /dev/null -w "%{http_code}" "https://cyba-op.vercel.app/api/auth/callback?code=test"
# Expected: 307 (redirect to /?error=auth_failed)
# NOT expected: 500

# Test 2: Check no "undefined" in redirect URL
curl -s -v "https://cyba-op.vercel.app/api/auth/callback?code=test" 2>&1 | grep Location
# Expected: Location: https://cyba-op.vercel.app/?error=auth_failed
# NOT expected: undefined/anything
```

---

### Requirement 2: Single Token Type — CybaOp JWT Only

**User Story:** As a platform operator, I want all authenticated requests to use a single token type (CybaOp JWT), so that the auth model is simple, auditable, and consistent.

#### Acceptance Criteria

1. THE Callback_Handler SHALL store only a CybaOp_JWT in the `cybaop_token` cookie; it SHALL NOT store a raw SC_Token as a fallback
2. WHEN the Backend `/auth/token-from-sc` is unavailable, THE Callback_Handler SHALL redirect to `{base_url}/?error=service_unavailable` — NOT store a raw SC_Token
3. THE Me_Proxy SHALL forward the `cybaop_token` cookie as `Authorization: Bearer {token}` to Backend `/auth/me`
4. IF Backend returns HTTP 401, THEN Me_Proxy SHALL return 401 and delete the `cybaop_token` cookie — NOT attempt to use the token as a SoundCloud token
5. THE Me_Proxy SHALL NOT contain any code path that calls the SoundCloud API directly

#### Verification

```bash
# Test: /me with no cookie returns 401
curl -s -w "%{http_code}" "https://cyba-op.vercel.app/api/auth/me"
# Expected: 401

# Test: /me with garbage token returns 401
curl -s -w "%{http_code}" -b "cybaop_token=garbage" "https://cyba-op.vercel.app/api/auth/me"
# Expected: 401
```

---

### Requirement 3: Backend Registration Endpoint Handles SC Token

**User Story:** As a developer, I want the Backend to accept an already-exchanged SoundCloud token, register the user, and issue a CybaOp JWT, so that the Vercel edge can exchange the code quickly without Railway cold-start latency killing the short-lived code.

#### Acceptance Criteria

1. WHEN POST `/auth/token-from-sc` receives `{ "access_token": "<valid_sc_token>" }`, THE Backend SHALL fetch profile, upsert user, return `AuthTokenResponse`
2. THE endpoint MUST be idempotent — same SoundCloud user MUST NOT create duplicate DB records
3. IF SoundCloud profile fetch fails, THEN return HTTP 502 with structured error
4. IF database upsert fails in production, THEN return HTTP 503 with structured error
5. THE endpoint SHALL respond within 10 seconds under normal conditions

#### Verification

```bash
# Test: Invalid SC token returns 502
curl -s -w "\n%{http_code}" -X POST \
  "https://delightful-beauty-production-7537.up.railway.app/auth/token-from-sc" \
  -H "Content-Type: application/json" \
  -d '{"access_token":"invalid"}'
# Expected: 502

# Test: Missing body returns 422
curl -s -w "\n%{http_code}" -X POST \
  "https://delightful-beauty-production-7537.up.railway.app/auth/token-from-sc" \
  -H "Content-Type: application/json" \
  -d '{}'
# Expected: 422
```

---

### Requirement 4: Analytics Pipeline Wired to API Endpoint

**User Story:** As a SoundCloud creator, I want the analytics pipeline to run when I request my analytics, so that I receive computed engagement metrics and insights based on my real track data.

#### Acceptance Criteria

1. WHEN authenticated GET `/analytics/insights` is called, THE Backend SHALL invoke the Analytics_Pipeline with the user's SC_Token from the database
2. THE pipeline SHALL execute `fetch_profile` and `fetch_tracks` for all tiers
3. WHEN tier is `free`, skip `generate_insights` (requires Gemini API key)
4. THE Backend SHALL return `AnalyticsResponse` with `success=true` and non-null `report`
5. IF pipeline raises an exception, return `AnalyticsResponse` with `success=false` and descriptive `message`
6. IF user's SC_Token is not in DB, return HTTP 401 with message "SoundCloud token not found — re-authenticate"

#### Verification

```bash
# Test: Unauthenticated returns 401
curl -s -w "\n%{http_code}" \
  "https://delightful-beauty-production-7537.up.railway.app/analytics/insights"
# Expected: 401

# Test: Valid JWT returns analytics (after successful auth)
curl -s -w "\n%{http_code}" \
  -H "Authorization: Bearer <valid_jwt>" \
  "https://delightful-beauty-production-7537.up.railway.app/analytics/insights"
# Expected: 200 with AnalyticsResponse
```

---

### Requirement 5: Frontend Analytics Proxy Route

**User Story:** As a developer, I want a Next.js API route that proxies analytics requests to the Backend, so that the JWT stays server-side.

#### Acceptance Criteria

1. THE Analytics_Proxy at `app/api/analytics/route.ts` SHALL extract `cybaop_token` cookie and forward as `Authorization: Bearer {token}` to Backend `/analytics/insights`
2. IF cookie is absent, return HTTP 401 without calling Backend
3. Forward Backend response status and JSON body unchanged
4. IF Backend unreachable, return HTTP 502

---

### Requirement 6: Analytics Page Renders Real Data

**User Story:** As a SoundCloud creator, I want the analytics page to display my actual engagement metrics and top tracks.

#### Acceptance Criteria

1. WHEN page loads, call Analytics_Proxy and show loading skeleton
2. WHEN response is successful with `metrics` field, render total plays, likes, comments, engagement rate
3. WHEN `metrics` is null (Free_Tier), render profile + track count only
4. WHEN response is an error, show error message + retry button
5. WHEN user is not authenticated (401), redirect to home page

---

### Requirement 7: Full Login-to-Analytics Flow

**User Story:** As a SoundCloud creator, I want to complete the full flow from "Connect SoundCloud" to seeing my analytics.

#### Acceptance Criteria

1. Click "Connect SoundCloud" → redirect to SoundCloud OAuth
2. Approve → callback exchanges code → registers user → sets cookie → redirect to `/dashboard`
3. Dashboard shows profile stats via Me_Proxy
4. Click "View Analytics" → analytics page shows real data

---

### Requirement 8: Production Hardening

**User Story:** As a platform operator, I want the system to handle errors gracefully, log structured events, and be observable.

#### Acceptance Criteria

1. CORS `allow_origins` includes `https://cyba-op.vercel.app` and `http://localhost:3000`
2. Rate limiting on all endpoints except `/health`, HTTP 429 with `Retry-After` header
3. All exception handlers emit structured log with `error_code`, `message`, `user_id`
4. `/health` returns 200 regardless of DB connectivity
5. DB unreachable at startup in development → log warning, continue running
6. Strip query params from Neon connection URL before passing to asyncpg

---

### Requirement 9: Debug Mode

**User Story:** As a developer, I want structured debug logging so I can diagnose failures without guessing.

#### Acceptance Criteria

1. WHEN `LOG_LEVEL=debug`, Callback_Handler MUST log: received code (first 8 chars), redirect_uri used, host header, final redirect URL
2. WHEN `LOG_LEVEL=debug`, Backend MUST log: SC token receipt (masked to first 8 chars), user_id, pipeline execution steps
3. ALL logs MUST be structured JSON (structlog on backend, console.error with context on frontend)

---

## Definition of Done

The system is complete when:

1. A new user can:
   - Click "Connect SoundCloud" on `cyba-op.vercel.app`
   - Successfully authenticate via SoundCloud OAuth
   - Land on `/dashboard` with their profile data displayed
   - Navigate to `/dashboard/analytics`
   - See real analytics data (at minimum: track list, play counts)

2. No 500 errors occur during the flow

3. All verification curl commands in Requirements 1-4 pass

4. Railway logs confirm:
   - Successful token receipt on `/auth/token-from-sc`
   - Successful user upsert in Neon Postgres
   - Successful analytics pipeline execution on `/analytics/insights`

5. Vercel logs confirm:
   - No "undefined" in any redirect URL
   - No raw SoundCloud tokens stored in cookies

### End-to-End Browser Verification

1. Open browser → `https://cyba-op.vercel.app`
2. Click "Connect SoundCloud"
3. Complete SoundCloud OAuth consent

Expected:
- Redirect to `/dashboard` (NOT home, NOT error page)
- Browser Network tab shows:
  - `/api/auth/callback` → 307 redirect
  - `/api/auth/me` → 200
- Cookie `cybaop_token` is present in browser (check DevTools → Application → Cookies)
- `/dashboard` renders username, followers, track count
- Click "View Analytics" → `/dashboard/analytics` loads
- Analytics page shows real data or "pipeline not connected" message (NOT a 500)

Failure conditions (any of these = NOT done):
- Any 500 error in the flow
- Missing `cybaop_token` cookie after auth
- Redirect URL contains "undefined"
- Dashboard shows "Not authenticated" after successful OAuth
- Analytics page crashes or shows blank
