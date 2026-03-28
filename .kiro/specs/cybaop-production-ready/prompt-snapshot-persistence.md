# Track Snapshot Persistence — Backend Only

Do NOT modify any frontend files. Backend only.
Do NOT guess. If a function signature doesn't match what's documented here, STOP and read the actual file.
Commit and push to `main` when done.

## PROBLEM

The analytics pipeline fetches live data from SoundCloud on every request, computes metrics, and discards the raw data. Nothing is persisted. This means:
- No trend detection over time (growth velocity requires historical snapshots)
- No milestone alerts (requires comparing current vs previous state)
- No engagement decay curves (requires time-series per track)
- Every analytics request costs 2+ SoundCloud API calls even if data hasn't changed

## WHAT EXISTS

### Database table (already created by schema.py):
```sql
CREATE TABLE IF NOT EXISTS track_snapshots (
    id BIGSERIAL PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES users(id),
    track_id TEXT NOT NULL,
    title TEXT NOT NULL DEFAULT '',
    play_count INT NOT NULL DEFAULT 0,
    like_count INT NOT NULL DEFAULT 0,
    comment_count INT NOT NULL DEFAULT 0,
    repost_count INT NOT NULL DEFAULT 0,
    captured_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

### Query function (already exists in queries.py):
```python
async def save_track_snapshots(user_id: str, tracks: list[dict[str, Any]]) -> int:
```
Expects: `[{"track_id": "123", "title": "...", "play_count": 0, "like_count": 0, "comment_count": 0, "repost_count": 0}]`

### Query function for reading (already exists):
```python
async def get_all_track_history(user_id: str, limit_per_track: int = 30) -> list[dict[str, Any]]:
```

### Pipeline state (AnalyticsState in state.py):
```python
class AnalyticsState(TypedDict):
    ...
    tracks_data: Optional[list[TrackData]]  # populated by fetch_tracks node
    snapshots: list[dict]  # currently always empty []
    ...
```

### TrackData model (models.py):
```python
class TrackData(BaseModel):
    platform_track_id: str
    title: str
    play_count: int = 0
    like_count: int = 0
    comment_count: int = 0
    repost_count: int = 0
    ...
```

## TASK 1: Save snapshots after pipeline completes

File: `backend/src/api/routes/analytics.py`

After `result = await graph.ainvoke(initial_state)` and before caching, add:

```python
# Persist track snapshots for trend detection
tracks_data = result.get("tracks_data") or []
if tracks_data:
    try:
        snapshot_records = [
            {
                "track_id": t.platform_track_id,
                "title": t.title,
                "play_count": t.play_count,
                "like_count": t.like_count,
                "comment_count": t.comment_count,
                "repost_count": t.repost_count,
            }
            for t in tracks_data
        ]
        await save_track_snapshots(user_id, snapshot_records)
    except Exception as e:
        logger.warning("snapshot_save_failed", user_id=user_id, error=str(e))
        # Non-fatal — analytics still returns successfully
```

Add `save_track_snapshots` to the imports from `src.db.queries`.

This MUST be non-fatal. If the DB write fails, analytics still returns. Log the failure as a warning, not an error.

## TASK 2: Load historical snapshots into pipeline state

File: `backend/src/api/routes/analytics.py`

Before `result = await graph.ainvoke(initial_state)`, load existing snapshots:

```python
# Load historical snapshots for trend detection
try:
    snapshots = await get_all_track_history(user_id)
except Exception:
    snapshots = []
```

Then pass them into `initial_state`:
```python
"snapshots": snapshots,  # was: []
```

Add `get_all_track_history` to the imports from `src.db.queries`.

## TASK 3: Deduplicate snapshots (max 1 per track per day)

File: `backend/src/db/queries.py`

The current `save_track_snapshots` inserts unconditionally. If a user refreshes analytics 10 times in a day, they get 10 snapshots per track. Fix this:

Replace the INSERT in `save_track_snapshots` with an upsert that only inserts if no snapshot exists for that (user_id, track_id) combination today:

```python
await conn.executemany(
    """INSERT INTO track_snapshots
       (user_id, track_id, title, play_count, like_count, comment_count, repost_count)
    SELECT $1, $2, $3, $4, $5, $6, $7
    WHERE NOT EXISTS (
        SELECT 1 FROM track_snapshots
        WHERE user_id = $1 AND track_id = $2
        AND captured_at >= date_trunc('day', NOW())
    )""",
    records,
)
```

## VERIFICATION

```bash
# After deploying, run analytics twice for the same user
# First run: should save snapshots (check Railway logs for "snapshots_saved")
# Second run within same day: should NOT create duplicate snapshots
# Check Neon DB: SELECT count(*) FROM track_snapshots; should equal track_count, not 2x
```

## CONSTRAINTS

- Do NOT modify any pipeline nodes (graph.py, calculate_metrics.py, etc.)
- Do NOT modify the frontend
- Do NOT change the AnalyticsResponse schema
- Snapshot persistence is NON-FATAL — never crash analytics because of a DB write failure
- All 39 existing tests must pass

## DEFINITION OF DONE

1. First analytics run for a user saves one snapshot per track to track_snapshots table
2. Subsequent runs on the same day do NOT create duplicate snapshots
3. Historical snapshots are loaded into pipeline state (enables future trend detection)
4. Railway logs show "snapshots_saved" with count on first run
5. No 500 errors, no broken analytics responses
6. 39/39 tests pass
