"""Tests for the triage engine."""

from datetime import datetime, timezone, timedelta

from src.shared.models import TrackData
from src.tools.triage import run_triage, Severity, IncidentType


def _track(
    tid: str = "1", title: str = "Test", plays: int = 1000,
    likes: int = 50, comments: int = 10, reposts: int = 20,
    created_days_ago: int = 30,
) -> TrackData:
    return TrackData(
        platform_track_id=tid,
        title=title,
        play_count=plays,
        like_count=likes,
        comment_count=comments,
        repost_count=reposts,
        created_at=datetime.now(timezone.utc) - timedelta(days=created_days_ago),
    )


def test_empty_catalog():
    report = run_triage([])
    assert report.overall_status == Severity.INFO
    assert report.incident_count == 1
    assert report.incidents[0].incident_type == IncidentType.STALE_CATALOG


def test_healthy_catalog():
    tracks = [
        _track("1", "Track A", plays=1000, likes=50, comments=10, reposts=20),
        _track("2", "Track B", plays=800, likes=40, comments=8, reposts=15),
        _track("3", "Track C", plays=600, likes=30, comments=6, reposts=12),
    ]
    report = run_triage(tracks)
    # No critical or warning incidents for a balanced catalog
    assert report.critical_count == 0
    assert report.catalog_uptime > 0


def test_concentration_risk():
    tracks = [
        _track("1", "Hit", plays=10000, likes=500, comments=100, reposts=200),
        _track("2", "Flop", plays=100, likes=5, comments=1, reposts=2),
    ]
    report = run_triage(tracks)
    conc = [i for i in report.incidents if i.incident_type == IncidentType.CONCENTRATION_RISK]
    assert len(conc) == 1
    assert conc[0].track_title == "Hit"


def test_underperformer_detection():
    tracks = [
        _track("1", "Normal A", plays=1000, likes=100, comments=20, reposts=30),
        _track("2", "Normal B", plays=1000, likes=100, comments=20, reposts=30),
        _track("3", "Bad Track", plays=1000, likes=5, comments=1, reposts=1),
    ]
    report = run_triage(tracks)
    under = [i for i in report.incidents if i.incident_type == IncidentType.UNDERPERFORMER]
    assert len(under) == 1
    assert under[0].track_title == "Bad Track"


def test_breakout_detection():
    tracks = [
        _track("1", "Normal", plays=1000, likes=10, comments=2, reposts=3),
        _track("2", "Normal 2", plays=1000, likes=10, comments=2, reposts=3),
        _track("3", "Viral", plays=1000, likes=200, comments=50, reposts=100),
    ]
    report = run_triage(tracks)
    breakouts = [i for i in report.incidents if i.incident_type == IncidentType.BREAKOUT]
    assert len(breakouts) == 1
    assert breakouts[0].track_title == "Viral"


def test_stale_catalog():
    tracks = [_track("1", "Old Track", created_days_ago=90)]
    report = run_triage(tracks)
    stale = [i for i in report.incidents if i.incident_type == IncidentType.STALE_CATALOG]
    assert len(stale) == 1
    assert report.last_release_days_ago >= 89


def test_silent_track():
    tracks = [
        _track("1", "Normal", plays=1000, likes=50, comments=10, reposts=20),
        _track("2", "Ghost", plays=0, likes=0, comments=0, reposts=0, created_days_ago=14),
    ]
    report = run_triage(tracks)
    silent = [i for i in report.incidents if i.incident_type == IncidentType.SILENT_TRACK]
    assert len(silent) == 1
    assert silent[0].track_title == "Ghost"


def test_severity_ordering():
    """Incidents should be sorted: critical > warning > info."""
    tracks = [
        _track("1", "Hit", plays=10000, likes=500, comments=100, reposts=200),
        _track("2", "Flop", plays=100, likes=5, comments=1, reposts=2),
        _track("3", "Bad", plays=1000, likes=2, comments=0, reposts=0, created_days_ago=90),
    ]
    report = run_triage(tracks)
    severities = [i.severity for i in report.incidents]
    order = {Severity.CRITICAL: 0, Severity.WARNING: 1, Severity.INFO: 2, Severity.HEALTHY: 3}
    assert severities == sorted(severities, key=lambda s: order[s])


def test_play_decay_detection():
    """Snapshot-based play decay should trigger incidents."""
    tracks = [_track("1", "Decaying Track", plays=500)]
    snapshots = [
        {"track_id": "1", "title": "Decaying Track", "play_count": 1000, "captured_at": datetime(2026, 3, 1, tzinfo=timezone.utc)},
        {"track_id": "1", "title": "Decaying Track", "play_count": 900, "captured_at": datetime(2026, 3, 5, tzinfo=timezone.utc)},
        {"track_id": "1", "title": "Decaying Track", "play_count": 800, "captured_at": datetime(2026, 3, 10, tzinfo=timezone.utc)},
        {"track_id": "1", "title": "Decaying Track", "play_count": 300, "captured_at": datetime(2026, 3, 15, tzinfo=timezone.utc)},
        {"track_id": "1", "title": "Decaying Track", "play_count": 200, "captured_at": datetime(2026, 3, 20, tzinfo=timezone.utc)},
        {"track_id": "1", "title": "Decaying Track", "play_count": 100, "captured_at": datetime(2026, 3, 25, tzinfo=timezone.utc)},
    ]
    report = run_triage(tracks, snapshots)
    decay = [i for i in report.incidents if i.incident_type == IncidentType.PLAY_DECAY]
    assert len(decay) == 1
    assert decay[0].severity in (Severity.WARNING, Severity.CRITICAL)
