"""Unit tests for the health score calculator."""

from datetime import datetime, timezone, timedelta

import pytest

from src.shared.models import AnalyticsMetrics, TrackData, TrendAnalysis
from src.tools.triage import TriageReport, Severity
from src.workflow.health import (
    HealthScoreResult,
    compute_health_score,
    is_significant_change,
)


def _make_metrics(
    avg_engagement_rate: float = 0.05,
    catalog_concentration: float = 0.4,
) -> AnalyticsMetrics:
    return AnalyticsMetrics(
        avg_engagement_rate=avg_engagement_rate,
        catalog_concentration=catalog_concentration,
    )


def _make_trends(growth_velocity_30d: float = 0.0) -> TrendAnalysis:
    return TrendAnalysis(growth_velocity_30d=growth_velocity_30d)


def _make_triage(critical: int = 0, warning: int = 0) -> TriageReport:
    return TriageReport(
        overall_status=Severity.HEALTHY,
        critical_count=critical,
        warning_count=warning,
    )


def _make_tracks(days_ago: int = 0) -> list[TrackData]:
    created = datetime.now(timezone.utc) - timedelta(days=days_ago)
    return [
        TrackData(
            platform_track_id="t1",
            title="Test Track",
            play_count=100,
            created_at=created,
        )
    ]


class TestComputeHealthScore:
    """Tests for compute_health_score()."""

    def test_all_components_perfect(self):
        """All components at max → score 100."""
        result = compute_health_score(
            metrics=_make_metrics(avg_engagement_rate=0.10, catalog_concentration=0.0),
            trends=_make_trends(growth_velocity_30d=0.5),
            triage_report=_make_triage(critical=0, warning=0),
            tracks=_make_tracks(days_ago=0),
        )
        assert result.score == 100
        assert result.missing_components == []
        assert all(v is not None for v in result.components.values())

    def test_all_components_zero(self):
        """All components at minimum → score 0."""
        result = compute_health_score(
            metrics=_make_metrics(avg_engagement_rate=0.0, catalog_concentration=1.0),
            trends=_make_trends(growth_velocity_30d=-0.5),
            triage_report=_make_triage(critical=4, warning=0),
            tracks=_make_tracks(days_ago=100),
        )
        assert result.score == 0
        assert result.missing_components == []

    def test_all_none_returns_zero(self):
        """All inputs None → score 0, all components missing."""
        result = compute_health_score(None, None, None, None)
        assert result.score == 0
        assert len(result.missing_components) == 5
        assert all(v is None for v in result.components.values())

    def test_partial_components(self):
        """Only metrics provided → partial score from engagement + diversity."""
        result = compute_health_score(
            metrics=_make_metrics(avg_engagement_rate=0.10, catalog_concentration=0.0),
            trends=None,
            triage_report=None,
            tracks=None,
        )
        # Both engagement (1.0) and diversity (1.0) are perfect
        # Re-normalized: (1.0*0.25 + 1.0*0.20) / (0.25 + 0.20) = 0.45/0.45 = 1.0 → 100
        assert result.score == 100
        assert set(result.missing_components) == {
            "release_cadence",
            "trend_momentum",
            "incident_severity",
        }

    def test_missing_components_tracked(self):
        """Missing components are listed correctly."""
        result = compute_health_score(
            metrics=None,
            trends=_make_trends(),
            triage_report=None,
            tracks=_make_tracks(),
        )
        assert "engagement_rate" in result.missing_components
        assert "catalog_diversity" in result.missing_components
        assert "incident_severity" in result.missing_components
        assert "trend_momentum" not in result.missing_components
        assert "release_cadence" not in result.missing_components

    def test_score_is_integer(self):
        """Score is always an integer."""
        result = compute_health_score(
            metrics=_make_metrics(avg_engagement_rate=0.03),
            trends=_make_trends(growth_velocity_30d=0.1),
            triage_report=_make_triage(critical=1, warning=2),
            tracks=_make_tracks(days_ago=45),
        )
        assert isinstance(result.score, int)
        assert 0 <= result.score <= 100

    def test_score_in_range(self):
        """Score is always in [0, 100]."""
        # Even with extreme values
        result = compute_health_score(
            metrics=_make_metrics(avg_engagement_rate=1.0, catalog_concentration=0.0),
            trends=_make_trends(growth_velocity_30d=10.0),
            triage_report=_make_triage(critical=0, warning=0),
            tracks=_make_tracks(days_ago=0),
        )
        assert 0 <= result.score <= 100

    def test_engagement_normalization(self):
        """5% engagement → 0.5 normalized."""
        result = compute_health_score(
            metrics=_make_metrics(avg_engagement_rate=0.05, catalog_concentration=0.5),
            trends=None,
            triage_report=None,
            tracks=None,
        )
        assert result.components["engagement_rate"] == pytest.approx(0.5)

    def test_engagement_capped_at_one(self):
        """Engagement above 10% still normalizes to 1.0."""
        result = compute_health_score(
            metrics=_make_metrics(avg_engagement_rate=0.20),
            trends=None,
            triage_report=None,
            tracks=None,
        )
        assert result.components["engagement_rate"] == 1.0

    def test_catalog_diversity_normalization(self):
        """concentration 0.4 → diversity 0.6."""
        result = compute_health_score(
            metrics=_make_metrics(catalog_concentration=0.4),
            trends=None,
            triage_report=None,
            tracks=None,
        )
        assert result.components["catalog_diversity"] == pytest.approx(0.6)

    def test_release_cadence_fresh(self):
        """Released today → cadence 1.0."""
        result = compute_health_score(
            metrics=None,
            trends=None,
            triage_report=None,
            tracks=_make_tracks(days_ago=0),
        )
        assert result.components["release_cadence"] == pytest.approx(1.0, abs=0.02)

    def test_release_cadence_stale(self):
        """Released 90+ days ago → cadence 0.0."""
        result = compute_health_score(
            metrics=None,
            trends=None,
            triage_report=None,
            tracks=_make_tracks(days_ago=100),
        )
        assert result.components["release_cadence"] == 0.0

    def test_trend_momentum_positive(self):
        """velocity 0.5 → momentum 1.0."""
        result = compute_health_score(
            metrics=None,
            trends=_make_trends(growth_velocity_30d=0.5),
            triage_report=None,
            tracks=None,
        )
        assert result.components["trend_momentum"] == 1.0

    def test_trend_momentum_negative(self):
        """velocity -0.5 → momentum 0.0."""
        result = compute_health_score(
            metrics=None,
            trends=_make_trends(growth_velocity_30d=-0.5),
            triage_report=None,
            tracks=None,
        )
        assert result.components["trend_momentum"] == 0.0

    def test_trend_momentum_neutral(self):
        """velocity 0.0 → momentum 0.5."""
        result = compute_health_score(
            metrics=None,
            trends=_make_trends(growth_velocity_30d=0.0),
            triage_report=None,
            tracks=None,
        )
        assert result.components["trend_momentum"] == pytest.approx(0.5)

    def test_incident_severity_clean(self):
        """No incidents → severity 1.0."""
        result = compute_health_score(
            metrics=None,
            trends=None,
            triage_report=_make_triage(critical=0, warning=0),
            tracks=None,
        )
        assert result.components["incident_severity"] == 1.0

    def test_incident_severity_critical(self):
        """1 critical → 1 - 0.3 = 0.7."""
        result = compute_health_score(
            metrics=None,
            trends=None,
            triage_report=_make_triage(critical=1, warning=0),
            tracks=None,
        )
        assert result.components["incident_severity"] == pytest.approx(0.7)

    def test_incident_severity_clamped(self):
        """Many incidents → clamped to 0.0."""
        result = compute_health_score(
            metrics=None,
            trends=None,
            triage_report=_make_triage(critical=5, warning=10),
            tracks=None,
        )
        assert result.components["incident_severity"] == 0.0

    def test_tracks_without_dates_treated_as_missing(self):
        """Tracks with no created_at → release_cadence missing."""
        tracks = [TrackData(platform_track_id="t1", title="No Date", play_count=100)]
        result = compute_health_score(None, None, None, tracks)
        assert "release_cadence" in result.missing_components
        assert result.components["release_cadence"] is None

    def test_empty_tracks_list_treated_as_missing(self):
        """Empty tracks list → release_cadence missing."""
        result = compute_health_score(None, None, None, [])
        assert "release_cadence" in result.missing_components

    def test_result_dataclass_fields(self):
        """HealthScoreResult has expected fields."""
        result = compute_health_score(None, None, None, None)
        assert hasattr(result, "score")
        assert hasattr(result, "components")
        assert hasattr(result, "missing_components")
        assert hasattr(result, "explanation")
        assert result.explanation is None


class TestIsSignificantChange:
    """Tests for is_significant_change()."""

    def test_large_increase(self):
        assert is_significant_change(40, 55) is True

    def test_large_decrease(self):
        assert is_significant_change(80, 60) is True

    def test_exactly_ten_not_significant(self):
        assert is_significant_change(50, 60) is False

    def test_exactly_eleven_significant(self):
        assert is_significant_change(50, 61) is True

    def test_no_change(self):
        assert is_significant_change(50, 50) is False

    def test_small_change(self):
        assert is_significant_change(50, 55) is False

    def test_boundary_negative(self):
        assert is_significant_change(60, 50) is False

    def test_boundary_negative_significant(self):
        assert is_significant_change(61, 50) is True
