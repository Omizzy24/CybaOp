# CybaOp UI Overhaul — Phase 1 (Mobile Layout, Analytics Charts, Animated Stats)

Do NOT refactor or modify any files in the `backend/` directory. Frontend only.

After each major change (landing page, dashboard, analytics), commit with a descriptive message before moving to the next page.

You are a senior frontend engineer implementing Phase 1 of CybaOp's UI overhaul. This phase covers mobile-responsive layout, analytics charts, and animated stat counters. Phase 2 (landing page redesign, shareable stats, onboarding) will be a separate prompt.

## SYSTEM CONTEXT

### Product
CybaOp is a live analytics intelligence platform for SoundCloud creators. Users log in with SoundCloud OAuth, see their profile stats on a dashboard, and view computed engagement metrics on an analytics page.

### Live URLs
- Frontend: https://cyba-op.vercel.app (Next.js 15, Vercel)
- Backend: https://delightful-beauty-production-7537.up.railway.app (FastAPI, Railway)

### Tech Stack
- Next.js 15 (App Router), React 18, Tailwind CSS v4, TypeScript
- Font: Geist (already loaded via next/font/google)
- Theme: Custom CSS vars in `app/globals.css` (--accent, --surface, --border, --muted)

### File Structure
```
app/
├── page.tsx                        # Landing page
├── layout.tsx                      # Root layout (Geist font, Tailwind)
├── globals.css                     # Theme variables
├── api/
│   ├── auth/
│   │   ├── soundcloud/route.ts     # OAuth initiation
│   │   ├── callback/route.ts       # OAuth callback
│   │   ├── me/route.ts             # Profile proxy
│   │   └── logout/route.ts         # Clear cookie
│   └── analytics/route.ts          # Analytics proxy
└── dashboard/
    ├── page.tsx                     # Dashboard (profile stats)
    └── analytics/page.tsx           # Analytics (metrics, tracks)
lib/
└── fetch.ts                        # Backend fetch wrapper
```

### Data Available from API
The analytics proxy (`/api/analytics`) returns:
```json
{
  "success": true,
  "report": {
    "track_count": 14,
    "metrics": {
      "total_plays": 2847,
      "total_likes": 42,
      "total_comments": 15,
      "total_reposts": 8,
      "avg_engagement_rate": 0.023,
      "catalog_concentration": 0.72,
      "all_track_metrics": [
        {
          "track_id": "123",
          "title": "artist-e",
          "engagement_rate": 0.008,
          "performance_score": 0.34,
          "plays_percentile": 0.85,
          "is_outlier": false,
          "outlier_direction": ""
        }
      ]
    },
    "trends": {
      "best_release_day": "Thursday",
      "best_release_hour": 14,
      "strongest_era_description": "Your strongest era: Mar 2025 to Jun 2025...",
      "confidence": 0.65
    },
    "top_tracks": [...],
    "tier": "free",
    "processing_time_ms": 1600,
    "nodes_executed": ["fetch_profile", "fetch_tracks", "calculate_metrics", "format_report"]
  }
}
```

The profile proxy (`/api/auth/me`) returns:
```json
{
  "user_id": "sc_288653846",
  "username": "omizzyy",
  "display_name": "Ohmizzy",
  "followers_count": 10,
  "following_count": 19,
  "track_count": 14,
  "likes_count": 474,
  "avatar_url": "https://i1.sndcdn.com/avatars-...-large.jpg",
  "tier": "free"
}
```

---

## PHASE 1 TASKS (in order)

### P1-TASK 1: Mobile-Responsive Layout [ENGINEERING]

Files to modify: `app/dashboard/page.tsx`, `app/dashboard/analytics/page.tsx`

**Engineering requirements:**
1. Replace the top `<nav>` with a bottom tab bar on mobile (< 768px)
   - Tabs: Dashboard, Analytics, Profile (3 tabs)
   - Fixed to bottom, 64px height, safe-area padding for notch phones
   - Active tab highlighted with accent color
   - On desktop (≥ 768px), keep the existing top nav
2. All card grids: `grid-cols-1` on mobile, `grid-cols-2` at `sm:`, `grid-cols-4` at `lg:`
3. Track performance table: horizontal scroll on mobile with sticky first column (track name)
4. No fixed-width containers — all flex/grid layouts
5. No `px` widths above 375px on any element
6. Test: resize browser to 375px width — no horizontal scrollbar, no overflow

**Design guidance:**
- Bottom nav should have subtle glassmorphism (backdrop-blur, semi-transparent bg)
- Tab icons: use emoji or simple SVG (📊 Dashboard, 📈 Analytics, 👤 Profile)
- Active tab: accent color underline, not background fill

**Commit after this task:** `"ui: mobile-responsive layout with bottom nav"`

---

### P1-TASK 2: Analytics Charts [ENGINEERING]

File to modify: `app/dashboard/analytics/page.tsx`
New dependency to install: `recharts` (run `npm install recharts`)

**Engineering requirements:**
1. Add a horizontal bar chart showing engagement rate per track (all tracks)
   - Y-axis: track titles (truncated to 20 chars)
   - X-axis: engagement rate (%)
   - Bars colored with accent gradient
   - Outlier tracks highlighted with different color
2. Add a donut chart showing genre distribution
   - Segments: count of tracks per genre
   - Center text: total track count
   - Use 5-6 distinct colors from the theme palette
3. Add a heatmap-style grid for release day performance
   - 7 columns (Mon-Sun)
   - Cell color intensity = average engagement for tracks released on that day
   - Highlight the best day with accent border
4. Charts must be responsive — full width on mobile, side-by-side on desktop where appropriate
5. Charts render from the data already returned by `/api/analytics` — no new API calls

**Design guidance:**
- Chart backgrounds: transparent (inherit card bg)
- Grid lines: subtle, use --border color
- Labels: use --muted color, Geist font
- Tooltips: dark bg, rounded, small text
- No chart legends that take up space — use inline labels or tooltips

**Commit after this task:** `"ui: analytics charts — engagement bars, genre donut, release heatmap"`

---

### P1-TASK 3: Animated Stat Counters [ENGINEERING]

Files to modify: `app/dashboard/page.tsx`, `app/dashboard/analytics/page.tsx`

**Engineering requirements:**
1. Create a `CountUp` component that animates numbers from 0 to target value
   - Duration: 1.2 seconds
   - Easing: ease-out
   - Use `requestAnimationFrame`, not setInterval
   - Trigger when element enters viewport (IntersectionObserver)
   - Format large numbers with commas (toLocaleString)
   - For percentages: animate to decimal, append "%"
2. Replace all static number displays in StatCard components with CountUp
3. No external animation libraries — pure CSS transitions + requestAnimationFrame

**Design guidance:**
- Numbers should use font-weight 700, font-variant-numeric: tabular-nums (prevents layout shift during animation)
- Slight scale-up effect (1.0 → 1.02 → 1.0) when animation completes
- Only animate on first viewport entry, not on every scroll

**Commit after this task:** `"ui: animated stat counters with viewport-triggered CountUp"`

---

## CONSTRAINTS

- Do NOT modify any files in `backend/`
- Do NOT modify `app/api/` routes (they work, don't touch them)
- Do NOT add Framer Motion — CSS transitions and requestAnimationFrame only
- Do NOT add a component library (no shadcn, no MUI, no Chakra)
- Do NOT add a state management library
- Use `recharts` for charts (not visx, not chart.js, not d3 directly)
- All pages must remain `"use client"` components
- Push to `main` branch for production deploy
- Commit after each task, not one big commit at the end

## KNOWN TRUTHS

- Tailwind v4 uses `@theme inline` in globals.css for custom properties
- `app/globals.css` already defines: --accent (#f97316), --surface (#141414), --border (#262626), --muted (#737373)
- The Geist font is loaded in `layout.tsx` via `next/font/google`
- All data comes from existing API routes — no backend changes needed
- The analytics page already has a loading skeleton — keep it

## STOP CONDITIONS

- If recharts doesn't install cleanly → STOP and report the error
- If the analytics API response shape doesn't match what's documented above → STOP and check the actual response
- If any existing functionality breaks (auth, data loading) → STOP and fix before continuing

## DEFINITION OF DONE (Phase 1)

1. Dashboard and analytics pages render correctly at 375px width — no horizontal scroll
2. Bottom tab bar visible on mobile, top nav on desktop
3. Analytics page has 3 charts: engagement bar chart, genre donut, release day heatmap
4. All stat numbers animate from 0 to target on first viewport entry
5. 3 separate commits (one per task)
6. All existing functionality still works (auth, dashboard data, analytics data)
7. No layout shifts during number animations (tabular-nums applied)
