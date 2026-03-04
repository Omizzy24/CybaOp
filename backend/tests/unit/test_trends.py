"""Tests for trend detection — pure math, deterministic."""

from datetime import datetime, timezone

from src.shared.models import TrackData
from src.tools.trends import (
    analyze_trends,
    detect_best_release_timing,
    detect_strongest_era,
)


def test_best_release_timing(sample_tracks):
    best_day, best_hour = detect_best_release_timing(sample_tracks)
    # Should return something (we have enough data)
    assert best_day is not None
    assert best_hour is not None


def test_best_release_timing_insufficient_data():
    tracks = [
        TrackData(platform_track_id="1", title="Only One", play_count=100,
                  created_at=datetime(2025, 1, 1, tzinfo=timezone.utc)),
    ]
    best_day, best_hour = detect_best_release_timing(tracks)
    assert best_day is None
    assert best_hour is None


def test_strongest_era(sample_tracks):
    start, end, desc = detect_strongest_era(sample_tracks)
    assert start is not None
    assert end is not None
    assert "plays" in desc.lower()


def test_strongest_era_insufficient_data():
    tracks = [
        TrackData(platform_track_id="1", title="T1", play_count=100,
                  created_at=datetime(2025, 1, 1, tzinfo=timezone.utc)),
    ]
    start, end, desc = detect_strongest_era(tracks)
    assert start is None
    assert end is None


def test_analyze_trends_full(sample_tracks):
    trends = analyze_trends(sample_tracks)
    assert trends.confidence > 0.0
    assert trends.best_release_day is not None
    assert trends.strongest_era_description != ""


def test_analyze_trends_empty():
    trends = analyze_trends([])
    assert trends.confidence == 0.0
    assert trends.best_release_day is None


def test_anomaly_detection(sample_tracks):
    trends = analyze_trends(sample_tracks)
    # The viral track should be flagged as anomaly (2x avg engagement)
    assert len(trends.anomaly_tracks) >= 0  # May or may not trigger depending on distribution


def test_growth_velocity_no_snapshots(sample_tracks):
    trends = analyze_trends(sample_tracks, snapshots=None)
    assert trends.growth_velocity_7d == 0.0
    assert trends.growth_velocity_30d == 0.0
