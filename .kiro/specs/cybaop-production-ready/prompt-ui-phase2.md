# CybaOp UI Overhaul — Phase 2 (Landing Page, Shareable Stats, Onboarding)

Do NOT refactor or modify any files in the `backend/` directory. Frontend only.

After each major change, commit with a descriptive message before moving to the next task.

Prerequisite: Phase 1 must be complete (mobile layout, charts, animated counters).

## SYSTEM CONTEXT

Same as Phase 1. Refer to `prompt-ui-phase1.md` for full system context, file structure, and API response shapes.

Key additions from Phase 1 that now exist:
- Bottom tab bar on mobile
- recharts installed and used for analytics charts
- CountUp component for animated numbers
- Mobile-responsive grid layouts

---

## PHASE 2 TASKS (in order)

### P2-TASK 1: Landing Page Redesign [ENGINEERING + DESIGN]

File to modify: `app/page.tsx`

**Engineering requirements:**
1. Full-viewport hero section with animated gradient background
   - CSS gradient animation (hue-rotate or position shift), no JS
   - Subtle floating particle effect using CSS keyframe animations (5-8 small circles, slow drift)
2. Hero content: "CybaOp" headline, tagline, "Connect SoundCloud" CTA
3. Social proof line: "Join 500+ SoundCloud creators"
4. Before/after comparison section:
   - Left: "What SoundCloud shows you" → screenshot-style card with raw play count
   - Right: "What CybaOp shows you" → card with engagement rate, best release day, outlier detection
5. Feature cards section (3 cards): Track Analytics, Trend Detection, AI Insights
6. Footer with minimal links
7. Fully responsive — stacks vertically on mobile

**Design guidance:**
- Background: deep black (#050505) with subtle radial gradient (accent color at 3% opacity)
- Floating particles: 2px circles, accent color at 10% opacity, CSS animation (translateY + opacity)
- CTA button: accent color, rounded-lg, subtle pulse animation on idle (scale 1.0 → 1.02, 2s loop)
- Before/after cards: glassmorphism (backdrop-blur-xl, bg-white/5, border border-white/10)
- Typography: "CybaOp" in text-6xl font-black, "Op" in accent color
- Social proof: small text, muted color, above the CTA
- No images — all CSS/SVG

**Commit:** `"ui: landing page redesign — hero, social proof, before/after, features"`

---

### P2-TASK 2: Shareable Stats Card [ENGINEERING]

New file: `app/dashboard/share/page.tsx`
New dependency: `html-to-image` (run `npm install html-to-image`)

**Engineering requirements:**
1. New page at `/dashboard/share` accessible from a "Share Your Stats" button on the dashboard
2. Renders a card (1080x1920 for Stories, with a toggle for 1200x675 for Twitter)
3. Card content:
   - CybaOp logo + branding
   - Username + avatar
   - Top stat: total plays
   - Top track: title + engagement rate
   - Best release day
   - "Powered by cyba-op.vercel.app" footer
4. "Download" button that converts the card div to PNG using html-to-image
5. Card uses the same dark theme as the app
6. Data comes from `/api/analytics` and `/api/auth/me` — no new API routes

**Design guidance:**
- Card background: gradient from #050505 to #0a0a0a
- Accent highlights on key numbers
- SoundCloud waveform-style decorative element (CSS, not image)
- Username in large text, stats in medium, branding in small
- Rounded corners on the card (for social media aesthetics)

**Commit:** `"ui: shareable stats card with PNG download"`

---

### P2-TASK 3: Onboarding Flow [ENGINEERING]

New file: `app/dashboard/onboarding.tsx` (component, not page)
File to modify: `app/dashboard/page.tsx`

**Engineering requirements:**
1. Create an onboarding overlay component that shows on first visit after login
2. Detection: check `localStorage.getItem("cybaop_onboarded")` — if null, show onboarding
3. 3 steps (advance with "Next" button or swipe on mobile):
   - Step 1: "Analyzing your catalog..." with a progress bar animation (CSS, fake progress over 2s)
   - Step 2: "Here's what we found" — show one highlight stat (e.g., total plays or best release day)
   - Step 3: "Your dashboard is ready" — CTA button "Explore" that closes onboarding
4. On completion: `localStorage.setItem("cybaop_onboarded", "true")`
5. Overlay: full-screen, dark bg with blur, centered card
6. Skip button in top-right corner

**Design guidance:**
- Progress bar: accent color, rounded, animated width
- Step transitions: fade + slide (CSS transitions, 300ms)
- Highlight stat: large number with CountUp animation
- "Explore" button: accent color, same style as landing page CTA
- Overlay bg: rgba(0,0,0,0.85) with backdrop-blur

**Commit:** `"ui: first-time onboarding flow with 3-step walkthrough"`

---

## CONSTRAINTS

- Do NOT modify any files in `backend/`
- Do NOT modify `app/api/` routes
- Do NOT modify `lib/fetch.ts`
- No Framer Motion — CSS transitions only
- Use `recharts` (already installed from Phase 1) if any charts needed
- Use `html-to-image` for the share card only
- Push to `main` branch
- Commit after each task

## STOP CONDITIONS

- If `html-to-image` doesn't install → use `dom-to-image-more` as fallback
- If the landing page gradient animation causes performance issues on mobile → simplify to static gradient
- If localStorage is not available (SSR) → wrap in `typeof window !== "undefined"` check

## DEFINITION OF DONE (Phase 2)

1. Landing page has animated hero, social proof, before/after section, feature cards
2. Share page generates downloadable PNG card with user stats
3. First-time users see onboarding overlay after login
4. Returning users skip onboarding (localStorage check)
5. 3 separate commits (one per task)
6. All existing functionality still works
7. Mobile-responsive on all new pages/components
