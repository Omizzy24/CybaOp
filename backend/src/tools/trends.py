"""Trend detection — pure math, no LLM. Moving averages, growth velocity, peak periods."""

from collections import defaultdict
from datetime import datetime, timezone

from src.shared.logging import get_logger
from src.shared.models import PeakPeriod, TrackData, TrendAnalysis

logger = get_logger("tools.trends")


def _growth_velocity(values: list[float], window: int) -> float:
    """Calculate growth velocity over a window of data points.
    Returns percentage change from start to end of window."""
    if len(values) < 2 or window < 1:
        return 0.0
    subset = values[-window:] if len(values) >= window else values
    if subset[0] == 0:
        return 0.0
    return (subset[-1] - subset[0]) / subset[0]


def _moving_average(values: list[float], window: int = 7) -> list[float]:
    """Simple moving average."""
    if len(values) < window:
        return values
    result = []
    for i in range(len(values) - window + 1):
        avg = sum(values[i:i + window]) / window
        result.append(avg)
    return result


def detect_best_release_timing(tracks: list[TrackData]) -> tuple[str | None, int | None]:
    """Analyze which day/hour releases perform best based on historical data."""
    if len(tracks) < 3:
        return None, None

    day_performance: dict[str, list[float]] = defaultdict(list)
    hour_performance: dict[int, list[float]] = defaultdict(list)

    for track in tracks:
        if not track.created_at or track.play_count == 0:
            continue
        day_name = track.created_at.strftime("%A")
        hour = track.created_at.hour
        # Use engagement as performance proxy
        engagement = (track.like_count + track.comment_count + track.repost_count)
        er = engagement / track.play_count if track.play_count > 0 else 0.0
        day_performance[day_name].append(er)
        hour_performance[hour].append(er)

    best_day = None
    best_hour = None

    if day_performance:
        avg_by_day = {d: sum(v) / len(v) for d, v in day_performance.items() if v}
        if avg_by_day:
            best_day = max(avg_by_day, key=avg_by_day.get)

    if hour_performance:
        avg_by_hour = {h: sum(v) / len(v) for h, v in hour_performance.items() if v}
        if avg_by_hour:
            best_hour = max(avg_by_hour, key=avg_by_hour.get)

    return best_day, best_hour


def detect_strongest_era(tracks: list[TrackData], window: int = 5) -> tuple[datetime | None, datetime | None, str]:
    """Find the period where tracks performed best (sliding window over release dates)."""
    dated = sorted(
        [t for t in tracks if t.created_at is not None],
        key=lambda t: t.created_at,
    )
    if len(dated) < window:
        return None, None, ""

    best_score = -1.0
    best_start = 0

    for i in range(len(dated) - window + 1):
        chunk = dated[i:i + window]
        total_engagement = sum(
            t.like_count + t.comment_count + t.repost_count for t in chunk
        )
        total_plays = sum(t.play_count for t in chunk)
        score = total_engagement / total_plays if total_plays > 0 else 0.0
        if score > best_score:
            best_score = score
            best_start = i

    era = dated[best_start:best_start + window]
    start_dt = era[0].created_at
    end_dt = era[-1].created_at
    top_track = max(era, key=lambda t: t.play_count)
    desc = (
        f"Your strongest era: {start_dt.strftime('%b %Y')} to {end_dt.strftime('%b %Y')}. "
        f"Top track: '{top_track.title}' with {top_track.play_count:,} plays."
    )
    return start_dt, end_dt, desc


def analyze_trends(
    tracks: list[TrackData],
    snapshots: list[dict] | None = None,
) -> TrendAnalysis:
    """Full trend analysis on the catalog."""
    confidence = min(1.0, len(tracks) / 20.0)  # More tracks = higher confidence

    # Growth velocity from snapshots (if available)
    gv_7d = 0.0
    gv_30d = 0.0
    gv_90d = 0.0
    accelerating = False

    if snapshots and len(snapshots) >= 2:
        # Aggregate total plays per snapshot day
        daily_plays: dict[str, int] = defaultdict(int)
        for s in snapshots:
            day_key = s["captured_at"].strftime("%Y-%m-%d") if hasattr(s["captured_at"], "strftime") else str(s["captured_at"])[:10]
            daily_plays[day_key] += s.get("play_count", 0)

        sorted_days = sorted(daily_plays.keys())
        play_series = [daily_plays[d] for d in sorted_days]

        gv_7d = _growth_velocity(play_series, 7)
        gv_30d = _growth_velocity(play_series, 30)
        gv_90d = _growth_velocity(play_series, 90)
        accelerating = gv_7d > gv_30d > 0

    # Release timing
    best_day, best_hour = detect_best_release_timing(tracks)

    # Strongest era
    era_start, era_end, era_desc = detect_strongest_era(tracks)

    # Anomaly tracks (engagement > 2x catalog average)
    if tracks:
        avg_er = sum(
            (t.like_count + t.comment_count + t.repost_count) / t.play_count
            for t in tracks if t.play_count > 0
        ) / max(1, sum(1 for t in tracks if t.play_count > 0))

        anomalies = [
            t.platform_track_id for t in tracks
            if t.play_count > 0
            and (t.like_count + t.comment_count + t.repost_count) / t.play_count > avg_er * 2
        ]
    else:
        anomalies = []

    return TrendAnalysis(
        growth_velocity_7d=round(gv_7d, 4),
        growth_velocity_30d=round(gv_30d, 4),
        growth_velocity_90d=round(gv_90d, 4),
        growth_accelerating=accelerating,
        best_release_day=best_day,
        best_release_hour=best_hour,
        anomaly_tracks=anomalies,
        strongest_era_start=era_start,
        strongest_era_end=era_end,
        strongest_era_description=era_desc,
        confidence=round(confidence, 2),
    )


def cluster_into_eras(tracks: list[TrackData], window_months: int = 6) -> list[dict]:
    """Group tracks into time-based eras (6-month windows) and compute per-era metrics."""
    dated = [t for t in tracks if t.created_at is not None]
    if not dated:
        return []

    dated.sort(key=lambda t: t.created_at)

    eras: dict[str, list[TrackData]] = defaultdict(list)
    for t in dated:
        year = t.created_at.year
        half = "H1" if t.created_at.month <= 6 else "H2"
        era_id = f"{year}-{half}"
        eras[era_id].append(t)

    result = []
    for era_id, era_tracks in eras.items():
        year = int(era_id.split("-")[0])
        is_h1 = era_id.endswith("H1")
        start = datetime(year, 1, 1, tzinfo=timezone.utc) if is_h1 else datetime(year, 7, 1, tzinfo=timezone.utc)
        end = datetime(year, 6, 30, tzinfo=timezone.utc) if is_h1 else datetime(year, 12, 31, tzinfo=timezone.utc)

        total_plays = sum(t.play_count for t in era_tracks)
        engagement_rates = []
        for t in era_tracks:
            if t.play_count > 0:
                er = (t.like_count + t.comment_count + t.repost_count) / t.play_count
                engagement_rates.append(er)

        avg_er = sum(engagement_rates) / len(engagement_rates) if engagement_rates else 0.0
        top = max(era_tracks, key=lambda t: t.play_count)
        genres = list({t.genre for t in era_tracks if t.genre})
        avg_dur = int(sum(t.duration_ms for t in era_tracks) / len(era_tracks)) if era_tracks else 0

        result.append({
            "era_id": era_id,
            "start": start,
            "end": end,
            "track_count": len(era_tracks),
            "total_plays": total_plays,
            "avg_engagement_rate": round(avg_er, 6),
            "top_track": top.title,
            "genres": genres,
            "avg_duration_ms": avg_dur,
        })

    result.sort(key=lambda e: e["start"], reverse=True)
    return result


def fingerprint_era(tracks: list[TrackData]) -> dict:
    """Extract the stylistic fingerprint of a set of tracks. Pure aggregation."""
    if not tracks:
        return {}

    genre_dist: dict[str, int] = defaultdict(int)
    for t in tracks:
        if t.genre:
            genre_dist[t.genre] += 1

    dominant = max(genre_dist, key=genre_dist.get) if genre_dist else ""
    avg_dur = int(sum(t.duration_ms for t in tracks) / len(tracks))
    avg_plays = sum(t.play_count for t in tracks) / len(tracks)

    engagement_rates = []
    for t in tracks:
        if t.play_count > 0:
            engagement_rates.append(
                (t.like_count + t.comment_count + t.repost_count) / t.play_count
            )
    avg_eng = sum(engagement_rates) / len(engagement_rates) if engagement_rates else 0.0

    return {
        "avg_duration_ms": avg_dur,
        "dominant_genre": dominant,
        "genre_distribution": dict(genre_dist),
        "avg_plays": round(avg_plays, 1),
        "avg_engagement": round(avg_eng, 6),
        "track_count": len(tracks),
    }
