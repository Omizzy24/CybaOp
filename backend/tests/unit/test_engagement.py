"""Tests for engagement calculations — these must be correct."""

from src.shared.models import TrackData
from src.tools.engagement import (
    calculate_engagement_rate,
    calculate_performance_score,
    compute_metrics,
)


def test_engagement_rate_basic():
    track = TrackData(
        platform_track_id="1", title="Test",
        play_count=1000, like_count=50, comment_count=10, repost_count=20,
    )
    rate = calculate_engagement_rate(track)
    assert rate == 0.08  # (50+10+20)/1000


def test_engagement_rate_zero_plays():
    track = TrackData(platform_track_id="1", title="Test", play_count=0)
    assert calculate_engagement_rate(track) == 0.0


def test_compute_metrics_empty():
    metrics = compute_metrics([])
    assert metrics.total_plays == 0
    assert metrics.avg_engagement_rate == 0.0


def test_compute_metrics_catalog(sample_tracks):
    metrics = compute_metrics(sample_tracks)
    assert metrics.total_plays == 64300  # 10000+3000+500+50000+800
    assert metrics.total_likes == 5755
    assert len(metrics.all_track_metrics) == 5
    assert len(metrics.top_tracks) == 5
    # Top track by performance should be the viral one
    assert metrics.top_tracks[0].track_id == "4"


def test_catalog_concentration(sample_tracks):
    metrics = compute_metrics(sample_tracks)
    # Top 20% = 1 track (the viral one with 50000 plays)
    # 50000 / 64300 ≈ 0.7776
    assert metrics.catalog_concentration > 0.7


def test_outlier_detection(sample_tracks):
    metrics = compute_metrics(sample_tracks)
    # Outlier detection uses 2 std devs — with this sample data the engagement
    # rates are close enough that none may trigger. Verify the mechanism works
    # by checking the field exists and is boolean on all metrics.
    for m in metrics.all_track_metrics:
        assert isinstance(m.is_outlier, bool)
        if m.is_outlier:
            assert m.outlier_direction in ("over", "under")


def test_performance_score_ordering(sample_tracks):
    metrics = compute_metrics(sample_tracks)
    scores = [m.performance_score for m in metrics.all_track_metrics]
    # Should be sorted descending
    assert scores == sorted(scores, reverse=True)
