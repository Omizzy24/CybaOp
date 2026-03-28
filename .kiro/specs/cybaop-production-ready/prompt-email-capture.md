# Pro Tier Email Capture — Frontend Only

Do NOT modify any files in `backend/`. Frontend only.
Do NOT add new API routes. Store emails client-side for now (localStorage), with a TODO for backend endpoint.
Commit and push to `main` when done.

## PROBLEM

The Pro feature teasers on the analytics page show locked cards but have no call-to-action. Users see "Pro" badges but can't do anything about it. There's no way to capture demand signal for the Pro tier before building it.

## WHAT EXISTS

File: `app/dashboard/analytics/page.tsx`

The `ProTeaser` component renders 3 cards:
- Engagement Decay Curves
- AI Release Strategy
- Competitor Benchmarking

Each card has: icon, title, description, "Pro" badge. No interaction.

## TASK 1: Add email capture to Pro teaser cards

File: `app/dashboard/analytics/page.tsx`

Modify the `ProTeaser` component to include a "Notify me" button. When clicked:
1. Show an inline email input field (replaces the button)
2. On submit: save to localStorage under key `cybaop_pro_waitlist`
3. Show confirmation: "You're on the list"
4. Store as JSON array: `[{"email": "...", "feature": "engagement_decay", "timestamp": "..."}]`

The email input MUST:
- Have `type="email"` for native validation
- Have `placeholder="your@email.com"`
- Submit on Enter key
- Show validation error for invalid email format
- Disable submit button while empty

After submission:
- Replace the input with a checkmark + "You're on the list"
- Persist across page reloads (check localStorage on mount)

## TASK 2: Add "Share Your Stats" CTA with email gate

File: `app/dashboard/page.tsx`

The dashboard already has a "Share Your Stats" link. No changes needed here — the share page exists at `/dashboard/share`.

## TASK 3: Add waitlist count to landing page

File: `app/page.tsx`

This is NOT possible with localStorage alone (it's per-device). Skip this task. The "Join 500+ SoundCloud creators" line stays as-is.

Add a TODO comment in the landing page:
```tsx
{/* TODO: Replace with real waitlist count from backend when /api/waitlist endpoint exists */}
```

## DATA SHAPE

localStorage key: `cybaop_pro_waitlist`
```json
[
  {
    "email": "user@example.com",
    "feature": "engagement_decay",
    "timestamp": "2026-03-27T15:00:00Z"
  }
]
```

## CONSTRAINTS

- Do NOT add a backend API endpoint (that's a separate task)
- Do NOT use any form library
- Do NOT send emails
- Do NOT add analytics/tracking scripts
- localStorage access MUST be wrapped in `typeof window !== "undefined"` check
- Email validation: use native HTML5 `type="email"` + basic regex check before submit
- All existing functionality must continue working

## VERIFICATION

1. Go to /dashboard/analytics
2. Scroll to Pro Features section
3. Click "Notify me" on any card
4. Enter email, submit
5. Page reload → card still shows "You're on the list"
6. Check DevTools → Application → localStorage → `cybaop_pro_waitlist` has the entry

## DEFINITION OF DONE

1. Each Pro teaser card has a "Notify me" button
2. Clicking shows inline email input
3. Valid email submission saves to localStorage
4. Confirmation persists across page reloads
5. No 500 errors, no broken layouts
6. Mobile-responsive (input fits within card on 375px)
