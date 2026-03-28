# CybaOp — Full System Synopsis + UI Overhaul Prompt

## PART 1: WHAT EXISTS (feed this to any agent for full context)

### Product
CybaOp is a live, working analytics intelligence platform for SoundCloud creators. It's deployed, authenticated users can log in with their SoundCloud account, and the analytics pipeline computes real engagement metrics from their track catalog.

### Live URLs
- Frontend: https://cyba-op.vercel.app (Next.js 15, Vercel)
- Backend: https://delightful-beauty-production-7537.up.railway.app (FastAPI, Railway)
- Database: Neon Postgres (serverless, us-east-1)

### Tech Stack
- Frontend: Next.js 15 (App Router), React 18, Tailwind CSS v4, TypeScript
- Backend: FastAPI, Python 3.11, asyncpg, Pydantic v2, structlog, httpx
- Pipeline: LangGraph StateGraph with 6 nodes (fetch_profile, fetch_tracks, calculate_metrics, detect_trends, generate_insights, format_report)
- Auth: SoundCloud OAuth → code exchange at Vercel edge → SC token sent to backend → JWT issued → httpOnly cookie
- Infra: Vercel (frontend), Railway (backend), Neon (Postgres), GitHub (source)

### What Works End-to-End
1. User clicks "Connect SoundCloud" → SoundCloud OAuth consent → redirect back → JWT cookie set → dashboard
2. Dashboard shows: username, display name, avatar, followers, following, tracks, likes
3. Analytics page shows: total plays, total likes, total comments, avg engagement rate, best release day, catalog health (concentration), strongest era, full track performance table with engagement rates + outlier detection
4. Pro feature teasers shown as locked cards (engagement decay, AI strategy, competitor benchmarking)
5. Logout clears cookie and redirects to home

### Architecture Boundaries
- Frontend is a thin transport layer — reads cookies, proxies to backend, renders data
- Backend owns ALL business logic: auth, user persistence, SoundCloud API calls, analytics pipeline
- One token type: CybaOp JWT. No fallback paths, no dual-token states
- All frontend→backend calls go through `lib/fetch.ts` (retry + timeout + backoff)
- All backend errors return structured JSON, never raw 500s

### File Structure (key files only)
```
app/
  page.tsx                          — Landing page (dark theme, CTA, feature cards)
  layout.tsx                        — Root layout (Geist font, Tailwind)
  globals.css                       — Theme vars (accent, surface, border, muted)
  api/
    auth/
      soundcloud/route.ts           — OAuth initiation (redirect to SoundCloud)
      callback/route.ts             — OAuth callback (code exchange, JWT, redirect)
      me/route.ts                   — Profile proxy (cookie → Bearer → backend)
      logout/route.ts               — Clear cookie
    analytics/route.ts              — Analytics proxy (cookie → Bearer → backend)
  dashboard/
    page.tsx                        — Dashboard (profile stats, analytics link)
    analytics/page.tsx              — Analytics (metrics, tracks, insights)
lib/
  fetch.ts                          — Backend fetch wrapper (retry, timeout)
backend/
  src/
    api/routes/auth.py              — /auth/token, /auth/token-from-sc, /auth/me, /auth/logout
    api/routes/analytics.py         — /analytics/insights (runs LangGraph pipeline)
    agent/graph.py                  — LangGraph StateGraph definition
    agent/nodes/                    — Pipeline nodes (6 files)
    tools/engagement.py             — Engagement math (rates, scores, concentration)
    tools/trends.py                 — Trend detection (release timing, strongest era)
    tools/soundcloud.py             — SoundCloud API wrapper (fetch profile, tracks)
    shared/models.py                — All Pydantic models (ProfileData, TrackData, etc.)
    db/queries.py                   — User CRUD, track snapshots
```

### Tier Feature Matrix (current)
| Feature | Free | Pro | Enterprise |
|---------|------|-----|------------|
| Catalog Overview (plays, likes, comments) | ✅ | ✅ | ✅ |
| Track Performance Table | ✅ | ✅ | ✅ |
| Best Release Window | ✅ | ✅ | ✅ |
| Catalog Health Check | ✅ | ✅ | ✅ |
| Strongest Era | ✅ | ✅ | ✅ |
| Outlier Detection | ✅ | ✅ | ✅ |
| Engagement Decay Curves | ❌ | ✅ | ✅ |
| AI Release Strategy | ❌ | ✅ | ✅ |
| Competitor Benchmarking | ❌ | ✅ | ✅ |
| Label Dashboard | ❌ | ❌ | ✅ |
| API Access | ❌ | ❌ | ✅ |

### Market Context
- SoundCloud: 180M users, 40M+ creators, broken native analytics
- Competitors: Chartmetric ($140/mo), Viberate ($20/mo), Soundcharts ($129/mo) — all multi-platform, none SoundCloud-native
- CybaOp's wedge: SoundCloud-native, free to start, AI-powered, pro-artist on AI trust
- Key pain points: vanity metrics with no strategy, broken stats, no release timing guidance, oversaturated market with no differentiation tools

---

## PART 2: UI OVERHAUL PROMPT

You are a senior product designer and frontend engineer. Your task is to transform CybaOp's frontend from a bare-bones developer prototype into a premium, addictive, mobile-first interface that feels like it belongs in 2030.

### Design Philosophy

CybaOp is NOT a dashboard tool. It's a creative intelligence companion. The UI should feel like:
- Spotify Wrapped meets Bloomberg Terminal meets Instagram Stories
- Dark, immersive, music-industry aesthetic
- Data visualization that's beautiful enough to screenshot and share
- Micro-interactions that make checking analytics feel rewarding
- Mobile-first — artists check this on their phone between sessions

### What's Wrong Now
1. Generic Tailwind dark theme — looks like every AI-generated SaaS
2. No personality, no brand voice, no emotional connection
3. Static cards with numbers — no motion, no delight, no storytelling
4. Desktop-only layout — not responsive, not mobile-optimized
5. No visual hierarchy — everything looks the same importance
6. No data visualization — just numbers in boxes
7. No onboarding flow — user lands on dashboard cold
8. No sharing/social features — artists can't flex their stats

### Design Requirements

#### 1. Visual Identity
- Color palette: Deep blacks (#050505), electric orange (#FF6B00) as accent, subtle gradients
- Typography: Geist (already loaded) — but use weight contrast aggressively (300 for body, 700 for headlines, 900 for hero numbers)
- Glassmorphism for cards (subtle blur, border opacity)
- Grain/noise texture overlay on backgrounds (subtle, not heavy)
- SoundCloud waveform motif as a recurring visual element

#### 2. Landing Page Redesign
- Hero: Full-viewport, animated gradient background with floating waveform particles
- Social proof: "Join 500+ SoundCloud creators" (even if aspirational)
- Before/after: Show what SoundCloud gives you (raw numbers) vs what CybaOp gives you (insights)
- CTA: Pulsing "Connect SoundCloud" button with SoundCloud orange
- Mobile: Stack vertically, large touch targets, swipeable feature cards

#### 3. Dashboard Redesign
- Top bar: Avatar, username, tier badge, notification bell (future), settings gear
- Hero stat: ONE big number that changes daily (e.g., "Your catalog was played 2,847 times this week" with animated counter)
- Quick insights: 3 swipeable cards with one-sentence insights ("Your best track this week is 'artist-e' — up 23%")
- Navigation: Bottom tab bar on mobile (Dashboard, Analytics, Releases, Profile)
- Pull-to-refresh on mobile

#### 4. Analytics Page Redesign
- Stat cards: Animated counters that tick up when they enter viewport
- Charts: 
  - Plays over time (area chart with gradient fill)
  - Engagement rate per track (horizontal bar chart)
  - Genre distribution (donut chart)
  - Release day performance (heatmap — days of week × time of day)
- Track table: Expandable rows — click a track to see its individual stats
- Outlier tracks: Highlighted with glow effect and "🔥 Outperforming" or "⚠️ Underperforming" badges
- Best Release Window: Visual clock/calendar showing optimal times
- Catalog Health: Visual meter (like a fuel gauge) showing concentration

#### 5. Micro-Interactions & Motion
- Page transitions: Smooth fade + slide between dashboard and analytics
- Number animations: CountUp effect on all stat numbers
- Card hover: Subtle lift + glow on desktop
- Loading states: Skeleton screens with shimmer animation (already have this, keep it)
- Pull-to-refresh: Custom animation with waveform
- Scroll-triggered animations: Cards fade in as they enter viewport

#### 6. Mobile-First Responsive
- All layouts must work on 375px width (iPhone SE)
- Bottom navigation bar (not top nav) on mobile
- Swipeable card carousels for insights
- Large touch targets (min 44px)
- No horizontal scrolling
- Sheet-style modals for track details (slide up from bottom)

#### 7. Shareable Stats (viral loop)
- "Share your stats" button that generates a card image (like Spotify Wrapped)
- Card includes: username, top track, total plays, engagement rate, CybaOp branding
- Optimized for Instagram Stories (1080x1920) and Twitter/X (1200x675)
- This is the growth engine — artists share, their followers see CybaOp branding

#### 8. Onboarding Flow (first-time user)
- After first login, show a 3-step welcome:
  1. "We're analyzing your catalog..." (with progress animation)
  2. "Here's what we found" (highlight one surprising insight)
  3. "Your dashboard is ready" (CTA to explore)
- This creates an emotional hook on first visit

### Technical Constraints
- Use Tailwind CSS v4 (already configured)
- Use Geist font (already loaded)
- For charts: use a lightweight library — recharts (React-native, ~45KB) or visx (lower level)
- For animations: use CSS transitions/animations first, Framer Motion only if needed
- For share cards: use html-to-image or similar for client-side image generation
- All pages must be `"use client"` components (they fetch data on mount)
- All data comes from existing API routes — no new backend changes needed
- Push to `main` branch for production deploy

### What NOT to Do
- Don't add a design system library (no Chakra, no MUI, no shadcn)
- Don't add a state management library (no Redux, no Zustand)
- Don't redesign the backend or API contracts
- Don't add authentication changes
- Don't add new API routes
- Don't over-animate — motion should enhance, not distract

### Priority Order
1. Mobile-responsive layout (bottom nav, stacked cards)
2. Analytics page charts (this is where users spend time)
3. Animated stat counters
4. Landing page redesign
5. Shareable stats card
6. Onboarding flow

### Definition of Done
1. All pages render correctly on mobile (375px) and desktop (1440px)
2. Analytics page has at least 2 real charts (plays over time, engagement per track)
3. Stat numbers animate on load
4. Landing page has visual personality (not generic Tailwind)
5. No layout shifts, no horizontal scroll on mobile
6. Lighthouse mobile score > 80
7. All existing functionality still works (auth, dashboard, analytics)
