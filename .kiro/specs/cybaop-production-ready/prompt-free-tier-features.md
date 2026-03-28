# CybaOp Free Tier Feature Implementation Prompt

You are a senior full-stack engineer implementing the free tier feature set for CybaOp — an analytics intelligence platform for SoundCloud creators.

## MARKET CONTEXT (why these features matter)

SoundCloud has 180M users and 40M+ creators. Existing analytics tools are either expensive ($20-140/mo) or built for labels. SoundCloud's own insights are broken (stats don't update, no actionable intelligence). Artists obsess over vanity metrics (play counts) but have zero strategy guidance.

CybaOp's wedge: SoundCloud-native, free to start, AI-powered insights that tell artists what to DO (not just what happened).

The free tier must deliver enough value that artists build a weekly habit of checking CybaOp. The goal is NOT to paywall everything — it's to make the free tier genuinely useful so artists trust the platform before upgrading.

## CURRENT STATE (what already works)

- OAuth: SoundCloud login → JWT → dashboard with real profile data ✅
- Backend: FastAPI on Railway, Neon Postgres, LangGraph pipeline ✅
- Analytics: Pipeline runs fetch_profile + fetch_tracks for free tier ✅
- Dashboard: Shows username, followers, tracks, likes ✅
- Analytics page: Shows "23 tracks analyzed, 3 pipeline stages" but no metrics for free tier ✅

The free tier currently shows "Detailed metrics are available on the Pro tier" — this is wrong. We need to give free users real value.

## TIER FEATURE LIST

### Free Tier — "Hook" (drives weekly return visits, no payment required)

| Feature | Description | Data Source | Compute Cost |
|---------|-------------|-------------|--------------|
| Catalog Overview | Total plays, likes, comments, reposts across all tracks | SoundCloud API /me/tracks | Low — sum aggregation |
| Track Performance Table | All tracks ranked by plays with engagement rate | SoundCloud API /me/tracks | Low — per-track math |
| Release Scorecard | 7-day performance report auto-generated per track | SoundCloud API + historical snapshots | Medium — needs snapshot comparison |
| Best Release Window | "Your tracks released on Thursdays get 2.3x more first-week plays" | Historical track created_at + play_count | Low — date grouping |
| Catalog Health Check | "3 of 14 tracks account for 70% of plays" (concentration metric) | SoundCloud API /me/tracks | Low — Pareto calculation |
| Milestone Alerts | "You hit 1,000 total plays" / "Followers grew 15% this month" | Historical snapshots vs current | Low — delta comparison |

### Pro Tier — "Depth" ($5-10/mo, worth paying for)

| Feature | Description | Why it's paid |
|---------|-------------|---------------|
| Engagement Decay Curves | How quickly plays drop off after release | Requires time-series snapshots over weeks |
| AI Release Strategy | "Based on your last 5 releases, here's what's working..." | Requires Gemini API (costs per call) |
| Competitor Benchmarking | Compare your metrics to 3-5 other artists | Requires fetching other artists' public data |
| Audience Overlap Analysis | Which of your tracks share listeners | Requires advanced SoundCloud API access |
| Repost/Collab Suggestions | Artists you should connect with based on genre/engagement | Requires cross-artist analysis |

### Enterprise Tier — (future, not implementing now)

| Feature | Description |
|---------|-------------|
| Label Dashboard | Multi-artist management |
| API Access | Programmatic access to analytics |
| Custom Reports | Scheduled email reports |

## WHAT TO IMPLEMENT NOW (this prompt)

Implement the 4 free tier features that require NO historical snapshots (we can add snapshot-based features later):

1. **Catalog Overview** — aggregate metrics across all tracks
2. **Track Performance Table** — all tracks ranked with engagement rates
3. **Best Release Window** — analyze created_at dates for optimal release timing
4. **Catalog Health Check** — concentration metric (what % of plays come from top 20% of tracks)

These 4 features use ONLY the data already fetched by the pipeline (fetch_profile + fetch_tracks). No new API calls needed.

## TASK 1: Update Pipeline Routing — Enable calculate_metrics for Free Tier

File: `backend/src/agent/edges/routing.py`

Current behavior: free tier skips `calculate_metrics` and goes straight to `format_report`.
New behavior: free tier runs `calculate_metrics` then `format_report` (still skips `detect_trends` and `generate_insights`).

```python
def route_by_tier(state: AnalyticsState) -> str:
    if state.get("error"):
        return "format_report"
    tier = state.get("tier", "free")
    if tier == "free":
        return "calculate_metrics"  # CHANGED: was "format_report"
    return "calculate_metrics"
```

Also update the graph to add a conditional edge from `calculate_metrics`:

File: `backend/src/agent/graph.py`

Change the edge from `calculate_metrics` → `detect_trends` to a conditional edge:
- free tier: `calculate_metrics` → `format_report`
- pro/enterprise: `calculate_metrics` → `detect_trends`

Add a new routing function in `routing.py`:

```python
def route_after_metrics(state: AnalyticsState) -> str:
    if state.get("error"):
        return "format_report"
    tier = state.get("tier", "free")
    if tier == "free":
        return "format_report"
    return "detect_trends"
```

## TASK 2: Add Best Release Window to calculate_metrics Node

File: `backend/src/agent/nodes/calculate_metrics.py`

After computing engagement metrics, add:

```python
# Best release window analysis
from collections import Counter
release_days = Counter()
for track in tracks:
    if track.created_at:
        day_name = track.created_at.strftime("%A")
        release_days[day_name] += track.play_count

# Find the day with highest average plays
if release_days:
    best_day = max(release_days, key=release_days.get)
```

Store `best_release_day` in the state or metrics object.

## TASK 3: Ensure format_report Includes All Free Tier Data

File: `backend/src/agent/nodes/format_report.py`

The report MUST include for free tier:
- `metrics.total_plays`, `total_likes`, `total_comments`, `total_reposts`
- `metrics.avg_engagement_rate`
- `metrics.catalog_concentration` (% of plays from top 20% of tracks)
- `metrics.all_track_metrics` (every track with engagement_rate and performance_score)
- `top_tracks` (top 5 by performance_score)
- `trends.best_release_day` (from the release window analysis)

Read `format_report.py` FIRST to understand what it currently includes.

## TASK 4: Update Analytics Page to Render Free Tier Data

File: `app/dashboard/analytics/page.tsx`

Now that free tier gets real metrics, update the page:

1. Remove the "Detailed metrics are available on the Pro tier" message
2. Show the 4-card stat grid: Total Plays, Total Likes, Total Comments, Avg Engagement
3. Show the full track performance table (all tracks, not just top 5)
4. Show "Best Release Window" card: "Your best release day is Thursday"
5. Show "Catalog Health" card: "Your top 3 tracks account for 72% of total plays"
6. For Pro-only features, show locked cards with descriptions (not a paywall wall — individual feature teasers)

### Layout:
```
[Stats Grid: 4 cards]
[Best Release Window card]  [Catalog Health card]
[Track Performance Table: all tracks]
[Pro Feature Teasers: 3 locked cards with descriptions]
```

## CONSTRAINTS

- DO NOT modify auth flow
- DO NOT add new Python dependencies
- DO NOT modify the LangGraph StateGraph structure (add_node, set_entry_point) — only modify edges and node internals
- Read existing node files BEFORE modifying them
- All changes must work with the existing AnalyticsState TypedDict
- Push to `main` branch for production deploy
- Test backend endpoint with curl after changes

## VERIFICATION

```bash
# Backend health
curl -s https://delightful-beauty-production-7537.up.railway.app/health

# Analytics with valid JWT should now return metrics for free tier
# (get a JWT by logging in at cyba-op.vercel.app, then extract from cookie)

# Frontend: login → dashboard → View Analytics should show:
# - 4 stat cards with real numbers
# - Track performance table
# - Best release window
# - Catalog health metric
```

## KNOWN TRUTHS

- SoundCloud field names: `playback_count` (not `plays_count`), `favoritings_count` (not `likes_count`)
- `calculate_metrics` uses `TrackData` from fetch_tracks — fields: play_count, like_count, comment_count, repost_count, duration_ms, genre, created_at
- The engagement tools in `backend/src/tools/engagement.py` already compute engagement_rate, catalog_concentration, and outlier detection — USE THEM, don't rewrite
- The trends tools in `backend/src/tools/trends.py` already compute best_release_timing — USE IT
- Push to `main` for production deploy

## STOP CONDITIONS

- If `calculate_metrics_node` doesn't have access to track data → STOP and check state flow
- If `AnalyticsState` needs new fields → add them to state.py TypedDict, don't use untyped dicts
- If any existing test breaks → fix the test, don't skip it
- If the engagement or trends tools don't exist where expected → STOP and ask

## DEFINITION OF DONE

1. Free tier user sees: total plays, total likes, total comments, avg engagement rate
2. Free tier user sees: all tracks ranked by performance with engagement rates
3. Free tier user sees: "Your best release day is [day]"
4. Free tier user sees: "Your top N tracks account for X% of total plays"
5. Pro features show as locked teasers, not a blank wall
6. No 500 errors
7. All 36 existing backend tests pass
