# Completion Engine — Full Stack

Do NOT guess. Read every file referenced before writing.
Do NOT add new Python dependencies except where specified.
Do NOT modify auth flow.
Commit after each task. Push to `main`.

Prerequisite: Era Intelligence must be deployed first (eras + fingerprint in analytics response).

## PROBLEM

CybaOp shows artists their data but doesn't answer: "What should I finish next?" Artists with large unreleased backlogs stall because of decision paralysis, not lack of motivation. The product must reduce project ambiguity by recommending ONE track to focus on, with a structured commitment mechanism.

## CORE LOOP

```
Connect SoundCloud
  → System identifies strongest era
  → System ranks unfinished tracks against era fingerprint
  → Shows ONE recommendation with reasoning
  → User accepts or overrides
  → 30-day Focus Mode activates
  → Weekly checkpoints
  → Mark complete or cancel (publicly within platform)
```

## TASK 1: Unfinished Tracks Input (Backend + Frontend)

### Backend

File: `backend/src/api/routes/tracks.py` (NEW)

New endpoint: `POST /tracks/unfinished`

```python
@router.post("/tracks/unfinished")
async def add_unfinished_tracks(
    request: UnfinishedTracksRequest,
    user: dict = Depends(get_current_user),
):
```

Request body:
```json
{
  "tracks": [
    {
      "title": "Grey Lights",
      "genre": "ambient",
      "bpm": 85,
      "notes": "started in 2024, feels unfinished"
    }
  ]
}
```

Add Pydantic models to `models.py`:
```python
class UnfinishedTrack(BaseModel):
    title: str
    genre: str = ""
    bpm: int = 0
    notes: str = ""

class UnfinishedTracksRequest(BaseModel):
    tracks: list[UnfinishedTrack]
```

Store in new DB table:
```sql
CREATE TABLE IF NOT EXISTS unfinished_tracks (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES users(id),
    title TEXT NOT NULL,
    genre TEXT NOT NULL DEFAULT '',
    bpm INT NOT NULL DEFAULT 0,
    notes TEXT NOT NULL DEFAULT '',
    alignment_score FLOAT,
    is_focus BOOLEAN NOT NULL DEFAULT FALSE,
    focus_started_at TIMESTAMPTZ,
    focus_deadline TIMESTAMPTZ,
    status TEXT NOT NULL DEFAULT 'pending',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

Add this table to `schema.py`.

### Frontend

File: `app/dashboard/unfinished/page.tsx` (NEW)

Onboarding-style page where user adds unfinished tracks:
1. Simple form: title (required), genre (optional), BPM (optional), notes (optional)
2. "Add Track" button adds to a list
3. "Save & Get Recommendation" submits all to backend
4. Minimum 3 tracks required before submission
5. After submission, redirect to `/dashboard/focus`

## TASK 2: Track Scoring Against Era Fingerprint (Backend)

File: `backend/src/tools/scoring.py` (NEW)

```python
def score_unfinished_tracks(
    unfinished: list[dict],
    fingerprint: dict,
) -> list[dict]:
    """Score each unfinished track against the strongest era fingerprint.
    
    Scoring (0-100):
    - Genre match: 40 points (exact match to dominant_genre)
    - BPM proximity: 30 points (closer to era avg = higher)
    - Title keyword overlap: 15 points (simple word overlap with era top tracks)
    - Recency: 15 points (newer = slightly higher)
    
    Returns sorted by score descending.
    """
```

This is a simple weighted scoring model. No ML. Deterministic. Explainable.

Each scored track gets:
```json
{
    "track_id": "...",
    "title": "Grey Lights",
    "alignment_score": 87.5,
    "reasoning": [
        "Genre matches your strongest era (ambient)",
        "BPM (85) is within your peak range (80-95)",
        "Similar title patterns to your top tracks"
    ]
}
```

The reasoning array is critical. Without it, the recommendation feels arbitrary.

## TASK 3: Recommendation Endpoint (Backend)

File: `backend/src/api/routes/tracks.py`

New endpoint: `GET /tracks/recommendation`

1. Get user's unfinished tracks from DB
2. Get user's era fingerprint (run analytics pipeline or read from cache)
3. Score all unfinished tracks
4. Return top 1 with reasoning

Response:
```json
{
    "recommendation": {
        "track_id": "...",
        "title": "Grey Lights",
        "alignment_score": 87.5,
        "reasoning": ["Genre matches...", "BPM within range..."],
        "era_reference": "2024 H1"
    },
    "alternatives": [
        {"track_id": "...", "title": "Northbound", "alignment_score": 72.3}
    ]
}
```

## TASK 4: Focus Mode (Backend)

File: `backend/src/api/routes/focus.py` (NEW)

Endpoints:
- `POST /focus/start` — Accept recommendation, start 30-day timer
- `GET /focus/status` — Current focus track, days remaining, checkpoints
- `POST /focus/complete` — Mark track as completed
- `POST /focus/cancel` — Cancel focus (resets, archives commitment)
- `POST /focus/extend` — Extend by 7 days (max 2 times)

Focus rules:
- Only 1 active focus at a time
- 30-day default deadline
- Max 2 extensions of 7 days each
- Cancel is allowed but resets streak
- Complete triggers celebration state

Store focus state in `unfinished_tracks` table (is_focus, focus_started_at, focus_deadline, status).

## TASK 5: Focus Mode UI (Frontend)

File: `app/dashboard/focus/page.tsx` (NEW)

When focus is active:
1. Hero card showing: track title, days remaining, progress bar
2. "Mark Complete" button (accent color, prominent)
3. "Extend" button (muted, only if extensions remaining)
4. "Cancel Focus" button (small, muted, bottom of page)
5. Weekly checkpoint prompts: "How's progress on 'Grey Lights'?" with 3 options: On Track / Behind / Stuck

When no focus active:
1. Show recommendation card with reasoning
2. "Accept & Start Focus" button
3. "Override" button (shows alternatives list)
4. Override triggers: "Switching focus archives this commitment. Are you sure?" modal

Dashboard integration:
- Add "Focus Mode" tab to bottom nav
- Dashboard page shows focus status banner if active

## CONSTRAINTS

- No new Python ML dependencies
- Scoring is deterministic weighted model, not ML
- Focus Mode is server-authoritative (not localStorage)
- All reasoning must be explicit strings, not black box scores
- Cancel must be possible but slightly friction-ful (confirmation modal)
- Mobile-responsive on all new pages
- All existing tests must pass

## VERIFICATION

```bash
# Add unfinished tracks
curl -s -X POST -H "Authorization: Bearer <jwt>" -H "Content-Type: application/json" \
  https://delightful-beauty-production-7537.up.railway.app/tracks/unfinished \
  -d '{"tracks":[{"title":"Grey Lights","genre":"ambient","bpm":85}]}'

# Get recommendation
curl -s -H "Authorization: Bearer <jwt>" \
  https://delightful-beauty-production-7537.up.railway.app/tracks/recommendation

# Start focus
curl -s -X POST -H "Authorization: Bearer <jwt>" -H "Content-Type: application/json" \
  https://delightful-beauty-production-7537.up.railway.app/focus/start \
  -d '{"track_id":"..."}'

# Check status
curl -s -H "Authorization: Bearer <jwt>" \
  https://delightful-beauty-production-7537.up.railway.app/focus/status
```

## DEFINITION OF DONE

1. User can add unfinished tracks via `/dashboard/unfinished`
2. System recommends ONE track with explicit reasoning
3. User can accept and enter 30-day Focus Mode
4. Focus page shows countdown, progress bar, checkpoint prompts
5. User can extend (max 2x), complete, or cancel
6. Cancel shows confirmation modal
7. Dashboard shows focus status banner
8. All existing tests pass
9. Mobile-responsive
