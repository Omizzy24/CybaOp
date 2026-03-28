# Era Intelligence — Backend + Frontend

Do NOT guess. Read every file referenced before writing.
Do NOT add new Python dependencies.
Do NOT modify auth flow or existing API contracts.
Commit after each task. Push to `main`.

## PROBLEM

CybaOp shows aggregate metrics but doesn't answer the core question: "When was I at my best, and what made that era different?" Artists need to see their creative evolution clustered into distinct periods, with the strongest era fingerprinted so unfinished work can be scored against it.

## WHAT EXISTS

- `backend/src/tools/trends.py` has `detect_strongest_era()` — returns start/end dates and description
- `backend/src/tools/engagement.py` has `compute_metrics()` — returns per-track engagement rates and performance scores
- `backend/src/agent/nodes/calculate_metrics.py` already calls both
- `backend/src/shared/models.py` has `TrendAnalysis` with `strongest_era_start`, `strongest_era_end`, `strongest_era_description`
- Track data includes: `play_count`, `like_count`, `comment_count`, `repost_count`, `genre`, `created_at`, `duration_ms`
- Frontend analytics page already shows "Your Strongest Era" as a text card

## TASK 1: Era Clustering (Backend)

File: `backend/src/tools/trends.py`

Add a new function `cluster_into_eras()`:

```python
def cluster_into_eras(tracks: list[TrackData], window_months: int = 6) -> list[dict]:
    """Group tracks into time-based eras and compute per-era metrics.
    
    Returns list of:
    {
        "era_id": "2024-H1",
        "start": datetime,
        "end": datetime,
        "track_count": int,
        "total_plays": int,
        "avg_engagement_rate": float,
        "top_track": str,
        "genres": list[str],
        "avg_duration_ms": int,
    }
    """
```

Logic:
1. Sort tracks by `created_at`
2. Group into 6-month windows (Jan-Jun = H1, Jul-Dec = H2)
3. For each window, compute: track count, total plays, avg engagement rate, dominant genres, avg duration
4. Identify top track per era by play_count
5. Return sorted by date descending

This is simple date bucketing + aggregation. No ML. No clustering algorithms. Deterministic.

## TASK 2: Era Fingerprint (Backend)

File: `backend/src/tools/trends.py`

Add a new function `fingerprint_era()`:

```python
def fingerprint_era(tracks: list[TrackData]) -> dict:
    """Extract the stylistic fingerprint of a set of tracks.
    
    Returns:
    {
        "avg_duration_ms": int,
        "dominant_genre": str,
        "genre_distribution": dict[str, int],
        "avg_plays": float,
        "avg_engagement": float,
        "track_count": int,
    }
    """
```

This takes the tracks from the strongest era and extracts their common traits. Pure aggregation.

## TASK 3: Wire into calculate_metrics node (Backend)

File: `backend/src/agent/nodes/calculate_metrics.py`

After existing metrics computation, add:

```python
from src.tools.trends import cluster_into_eras, fingerprint_era

eras = cluster_into_eras(tracks)

# Find strongest era by avg_engagement_rate
strongest = max(eras, key=lambda e: e["avg_engagement_rate"]) if eras else None

# Get fingerprint of strongest era tracks
if strongest:
    era_tracks = [t for t in tracks if t.created_at and strongest["start"] <= t.created_at <= strongest["end"]]
    fingerprint = fingerprint_era(era_tracks)
```

Store in state. Add `eras` and `era_fingerprint` to `AnalyticsState` TypedDict in `state.py`:

```python
eras: list[dict]
era_fingerprint: Optional[dict]
```

## TASK 4: Include eras in report (Backend)

File: `backend/src/agent/nodes/format_report.py`

Add eras to the `AnalyticsReport`. First add to `models.py`:

```python
class EraData(BaseModel):
    era_id: str
    start: datetime
    end: datetime
    track_count: int = 0
    total_plays: int = 0
    avg_engagement_rate: float = 0.0
    top_track: str = ""
    genres: list[str] = []
    avg_duration_ms: int = 0
```

Add to `AnalyticsReport`:
```python
eras: list[EraData] = []
era_fingerprint: Optional[dict] = None
```

In `format_report_node`, populate from state.

## TASK 5: Render eras on analytics page (Frontend)

File: `app/dashboard/analytics/page.tsx`

Replace the single "Your Strongest Era" text card with an era timeline:

1. Show all eras as horizontal cards in a scrollable row
2. Each card shows: era name (e.g., "2024 H1"), track count, total plays, avg engagement
3. Strongest era highlighted with accent border
4. Below the timeline, show the era fingerprint: dominant genre, avg duration, avg engagement

Layout:
```
[Era Timeline: scrollable horizontal cards]
[Strongest Era Fingerprint: 3-4 stat cards]
```

Update the `AnalyticsData` TypeScript interface to include `eras` and `era_fingerprint` from the API response.

## CONSTRAINTS

- No new Python dependencies
- No ML libraries — this is pure date bucketing and aggregation
- Era windows are fixed 6-month periods, not dynamic clustering
- All existing tests must pass
- Frontend changes must be mobile-responsive

## VERIFICATION

```bash
# Backend: analytics response should now include "eras" array and "era_fingerprint" object
curl -s -H "Authorization: Bearer <jwt>" \
  https://delightful-beauty-production-7537.up.railway.app/analytics/insights | python3 -m json.tool | grep -A5 "eras"
```

## DEFINITION OF DONE

1. Analytics response includes `eras` array with per-era metrics
2. Analytics response includes `era_fingerprint` for strongest era
3. Frontend shows era timeline with strongest era highlighted
4. Frontend shows era fingerprint stats
5. All existing tests pass
6. Mobile-responsive
