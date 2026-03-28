# Implementation Plan: Launch-Ready MVP

## Overview

Incremental frontend-only changes to prepare CybaOp for public launch. Ordered for safe, progressive delivery: SEO metadata first (zero visual risk), then OAuth flow hardening, then the landing page restructure, then env docs, then final verification. No backend code is modified — all 77 backend tests remain unaffected.

## Tasks

- [ ] 1. Add SEO and social sharing meta tags to root layout
  - [ ] 1.1 Expand the `metadata` export in `app/layout.tsx` with `metadataBase`, `alternates.canonical`, full `openGraph` object (`og:title`, `og:description`, `og:image`, `og:url`, `og:type`, `siteName`), and `twitter` card object (`card`, `title`, `description`, `images`)
    - Use `/og-image.png` as the image path (placeholder — actual image can be added later)
    - Set `metadataBase` to `https://cyba-op.vercel.app`
    - Update `description` to mention analytics intelligence, engagement rates, trend detection, and AI-powered insights
    - _Requirements: 5.1, 5.2, 5.3, 5.4_

- [ ] 2. Harden OAuth flow — Me route, health check, callback, logout
  - [ ] 2.1 Remove SC token fallback from `/api/auth/me`
    - Delete the `fetchFromSoundCloud` helper function entirely from `app/api/auth/me/route.ts`
    - On backend 401: return 401 to client and delete `cybaop_token` cookie
    - On backend unreachable (catch block): return 503 with `{ "error": "Profile service unavailable" }`
    - On backend 5xx: return 502 with `{ "error": "Failed to fetch profile" }`
    - Never call `api.soundcloud.com` from this route
    - _Requirements: 7.1, 7.2, 7.3, 7.4_

  - [ ]* 2.2 Write property tests for Me route (Properties 1, 2, 3)
    - Set up vitest + fast-check as dev dependencies (`vitest`, `fast-check`, `@vitejs/plugin-react`)
    - Create `vitest.config.ts` at project root
    - **Property 1: Me route uses only JWT backend auth** — for random token strings, mock `backendFetch`, assert no calls to `api.soundcloud.com`
    - **Validates: Requirements 7.1, 7.2**
    - **Property 2: Me route clears cookie on backend 401** — mock backend returning 401, assert response is 401 with `Set-Cookie` header deleting `cybaop_token`
    - **Validates: Requirements 7.3**
    - **Property 3: Me route returns 503 when backend unreachable** — mock backend throwing network errors, assert 503 with correct body
    - **Validates: Requirements 7.4**

  - [ ] 2.3 Create health check proxy at `app/api/health/route.ts`
    - GET handler calls `backendFetch("/health", { timeoutMs: 5000, retries: 0 })`
    - On success: return 200 `{ "status": "ok", "backend": "reachable" }`
    - On error/timeout: return 503 `{ "status": "degraded", "backend": "unreachable" }`
    - _Requirements: 8.1, 8.2, 8.3, 8.4_

  - [ ]* 2.4 Write property test for health check (Property 4)
    - **Property 4: Health check reflects backend reachability** — generate random backend responses (200, 500, timeout), assert correct status/body mapping
    - **Validates: Requirements 8.2, 8.3**

  - [ ] 2.5 Fix callback route missing-code handling
    - In `app/api/auth/callback/route.ts`, change the missing `code` param case from returning JSON 400 to redirecting to `/?error=exchange_failed`
    - All other error redirects are already correct (`error=timeout`, `error=auth_failed`, `error=service_unavailable`)
    - _Requirements: 9.1, 9.2, 9.3, 9.4_

  - [ ]* 2.6 Write property test for callback error mapping (Property 5)
    - **Property 5: Callback route maps failure modes to correct error redirects** — generate random failure scenarios, assert correct error code in redirect URL
    - **Validates: Requirements 9.1, 9.2, 9.4**

  - [ ] 2.7 Verify logout route implementation
    - Confirm `app/api/auth/logout/route.ts` deletes `cybaop_token` cookie and returns `{ "success": true }` (already implemented — no changes expected)
    - _Requirements: 12.1, 12.2, 12.3_

  - [ ]* 2.8 Write property test for logout cookie deletion (Property 7)
    - **Property 7: Logout deletes session cookie** — assert POST to `/api/auth/logout` always returns response with cookie deletion header
    - **Validates: Requirements 12.2**

- [ ] 3. Checkpoint — OAuth flow hardening
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 4. Restructure landing page
  - [ ] 4.1 Add auth redirect and loading state to landing page
    - Add `isCheckingAuth` state — on mount, call `fetch("/api/auth/me")`, if 200 redirect to `/dashboard` via `router.push`
    - Add `isConnecting` state — on CTA click, set true, change button text to "Connecting...", disable button, then `window.location.href = "/api/auth/soundcloud"`
    - Import `useRouter` and `useEffect` (already using `useSearchParams`)
    - _Requirements: 10.1, 10.2, 11.1, 11.2_

  - [ ]* 4.2 Write property test for authenticated user redirect (Property 6)
    - **Property 6: Authenticated users are redirected from landing page** — mock `/api/auth/me` returning 200, assert redirect to `/dashboard`
    - **Validates: Requirements 11.1**

  - [ ] 4.3 Restructure hero section and value proposition
    - Replace "Join 500+ SoundCloud creators" with honest copy (e.g. "Built for independent SoundCloud artists")
    - Ensure primary headline communicates core value proposition
    - Ensure subheadline explains what CybaOp does in concrete terms (analytics, trends, insights)
    - Add "Try again" link to error messages pointing to `/api/auth/soundcloud`
    - _Requirements: 1.1, 1.2, 1.4, 9.5, 9.6_

  - [ ] 4.4 Add "How it works" section
    - Three steps: Connect → Analyze → Act
    - Place between hero and feature cards sections
    - _Requirements: 1.3_

  - [ ] 4.5 Expand feature cards section
    - Update existing 3 cards (Track Analytics, Trend Detection, AI Insights) to match requirement descriptions: engagement rates + outlier detection, release timing + growth velocity, personalized recommendations
    - Add references to triage and workflow capabilities
    - _Requirements: 3.1, 3.3_

  - [ ] 4.6 Update comparison section
    - Ensure SoundCloud vs CybaOp comparison includes: engagement rate, best release day, top track performance, and catalog health score (already mostly present — verify and adjust)
    - _Requirements: 3.2_

  - [ ] 4.7 Add trust signals section
    - Display "Read-only access", "No data stored on third parties", "Open analytics" as trust signal items
    - Add social proof text targeting independent SoundCloud artists without fabricating user counts
    - Ensure "Read-only access. We never modify your account." text is adjacent to primary CTA
    - _Requirements: 2.1, 2.2, 2.3_

  - [ ] 4.8 Add secondary CTA and update footer
    - Add a secondary "Connect SoundCloud" CTA above the footer linking to `/api/auth/soundcloud`
    - Add Privacy Policy and Terms of Service links to footer (placeholder hrefs acceptable)
    - Ensure footer has CybaOp copyright and "Built for SoundCloud creators" tagline
    - _Requirements: 4.1, 4.2, 4.3_

  - [ ] 4.9 Ensure mobile-first responsive layout
    - Hero, feature cards, comparison, and CTAs render single-column on viewports < 640px
    - Font sizes, padding, spacing maintain readability without horizontal scroll on mobile
    - CTA buttons have minimum 44x44px touch target on mobile
    - _Requirements: 6.1, 6.2, 6.3_

- [ ] 5. Checkpoint — Landing page restructure
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 6. Document environment variables
  - [ ] 6.1 Create `.env.example` at project root for frontend (Vercel) variables
    - List `SOUNDCLOUD_CLIENT_ID`, `SOUNDCLOUD_CLIENT_SECRET`, `SOUNDCLOUD_REDIRECT_URI`, `BACKEND_URL` as required with example values
    - List `LOG_LEVEL` as optional
    - Mark required vs optional and provide descriptions
    - _Requirements: 13.1, 13.3_

  - [ ] 6.2 Update `backend/.env.example` with complete backend variable documentation
    - Ensure all required vars are listed: `SOUNDCLOUD_CLIENT_ID`, `SOUNDCLOUD_CLIENT_SECRET`, `JWT_SECRET`, `DATABASE_URL`, `FRONTEND_URL`
    - Ensure optional vars are listed with defaults: `JWT_ALGORITHM`, `JWT_EXPIRY_HOURS`, `GOOGLE_API_KEY`, `API_PORT`, `API_HOST`, `ENV`, `LOG_LEVEL`, `RATE_LIMIT_PER_MINUTE`, `CACHE_TTL_PROFILE`, `CACHE_TTL_TRACKS`, `CACHE_TTL_INSIGHTS`
    - Add comments marking required vs optional with example values
    - _Requirements: 13.2, 13.3_

- [ ] 7. Final checkpoint — Full verification
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- All changes are frontend-only — no backend code is modified, so all 77 backend pytest tests remain unaffected
- The build uses `--no-lint`, so linting issues won't block deployment
- Property tests require setting up vitest + fast-check (task 2.2), which is optional
- Each task references specific requirements for traceability
- Checkpoints at tasks 3, 5, and 7 ensure incremental validation
