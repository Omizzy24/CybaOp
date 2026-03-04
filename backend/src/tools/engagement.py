"""Engagement calculations — pure math, no LLM, fully deterministic."""

import statistics

from src.shared.logging import get_logger
from src.shared.models import AnalyticsMetrics, TrackData, TrackMetrics

logger = get_logger("tools.engagement")


def calculate_engagement_rate(track: TrackData) -> float:
    """(likes + comments + reposts) / plays. Returns 0 if no plays."""
    if track.play_count == 0:
        return 0.0
    return (track.like_count + track.comment_count + track.repost_count) / track.play_count


def calculate_performance_score(track: TrackData, avg_plays: float) -> float:
    """Weighted composite score: 50% engagement, 30% plays relative to avg, 20% comments."""
    engagement = calculate_engagement_rate(track)
    plays_ratio = track.play_count / avg_plays if avg_plays > 0 else 0.0
    comment_ratio = track.comment_count / track.play_count if track.play_count > 0 else 0.0

    return (engagement * 0.5) + (min(plays_ratio, 5.0) / 5.0 * 0.3) + (min(comment_ratio, 0.1) / 0.1 * 0.2)


def compute_metrics(tracks: list[TrackData]) -> AnalyticsMetrics:
    """Compute full analytics metrics across the catalog."""
    if not tracks:
        return AnalyticsMetrics()

    total_plays = sum(t.play_count for t in tracks)
    total_likes = sum(t.like_count for t in tracks)
    total_comments = sum(t.comment_count for t in tracks)
    total_reposts = sum(t.repost_count for t in tracks)

    avg_plays = total_plays / len(tracks) if tracks else 0.0
    play_counts = sorted([t.play_count for t in tracks], reverse=True)

    # Catalog concentration: % of plays from top 20% of tracks
    top_20_count = max(1, len(tracks) // 5)
    top_20_plays = sum(play_counts[:top_20_count])
    concentration = top_20_plays / total_plays if total_plays > 0 else 0.0

    # Per-track metrics
    all_metrics: list[TrackMetrics] = []
    engagement_rates: list[float] = []

    for track in tracks:
        er = calculate_engagement_rate(track)
        engagement_rates.append(er)
        ps = calculate_performance_score(track, avg_plays)

        all_metrics.append(TrackMetrics(
            track_id=track.platform_track_id,
            title=track.title,
            engagement_rate=round(er, 6),
            comment_to_play_ratio=round(
                track.comment_count / track.play_count if track.play_count > 0 else 0.0, 6
            ),
            repost_to_like_ratio=round(
                track.repost_count / track.like_count if track.like_count > 0 else 0.0, 6
            ),
            performance_score=round(ps, 4),
        ))

    # Detect outliers (> 2 std devs from mean engagement)
    if len(engagement_rates) >= 3:
        mean_er = statistics.mean(engagement_rates)
        stdev_er = statistics.stdev(engagement_rates)
        if stdev_er > 0:
            for i, m in enumerate(all_metrics):
                z = (m.engagement_rate - mean_er) / stdev_er
                if abs(z) > 2.0:
                    all_metrics[i] = m.model_copy(update={
                        "is_outlier": True,
                        "outlier_direction": "over" if z > 0 else "under",
                    })

    # Percentiles
    if play_counts:
        for m in all_metrics:
            track = next(t for t in tracks if t.platform_track_id == m.track_id)
            rank = sum(1 for p in play_counts if p <= track.play_count)
            m.plays_percentile = round(rank / len(play_counts), 4)

    # Sort by performance score
    all_metrics.sort(key=lambda m: m.performance_score, reverse=True)
    avg_er = statistics.mean(engagement_rates) if engagement_rates else 0.0

    return AnalyticsMetrics(
        total_plays=total_plays,
        total_likes=total_likes,
        total_comments=total_comments,
        total_reposts=total_reposts,
        avg_engagement_rate=round(avg_er, 6),
        catalog_concentration=round(concentration, 4),
        top_tracks=all_metrics[:10],
        all_track_metrics=all_metrics,
    )
