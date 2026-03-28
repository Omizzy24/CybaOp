"""Health Score calculator — pure computation, no I/O.

Computes a weighted composite score (0-100) from engagement rate,
catalog diversity, release cadence, trend momentum, and incident severity.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone

from src.shared.models import AnalyticsMetrics, TrackData, TrendAnalysis
from src.tools.triage import TriageReport


# Component weights
WEIGHTS: dict[str, float] = {
    "engagement_rate": 0.25,
    "catalog_diversity": 0.20,
    "release_cadence": 0.20,
    "trend_momentum": 0.20,
    "incident_severity": 0.15,
}


@dataclass
class HealthScoreResult:
    score: int  # 0-100
    components: dict[str, float | None]  # component name → normalized 0-1 value (None if missing)
    missing_components: list[str] = field(default_factory=list)
    explanation: str | None = None  # AI-generated if score changed significantly


def _normalize_engagement_rate(metrics: AnalyticsMetrics) -> float:
    """min(rate / 0.10, 1.0) — 10% engagement = perfect score."""
    return min(metrics.avg_engagement_rate / 0.10, 1.0)


def _normalize_catalog_diversity(metrics: AnalyticsMetrics) -> float:
    """1 - catalog_concentration. 0 = all plays on one track, 1 = even spread."""
    return 1.0 - metrics.catalog_concentration


def _normalize_release_cadence(tracks: list[TrackData]) -> float:
    """max(0, 1 - days_since / 90) — 0 days = 1.0, 90+ days = 0.0."""
    now = datetime.now(timezone.utc)
    dated = [t for t in tracks if t.created_at is not None]
    if not dated:
        return 0.0
    latest = max(t.created_at for t in dated)
    if latest.tzinfo is None:
        days_since = (now.replace(tzinfo=None) - latest).days
    else:
        days_since = (now - latest).days
    return max(0.0, 1.0 - days_since / 90.0)


def _normalize_trend_momentum(trends: TrendAnalysis) -> float:
    """min(max(velocity + 0.5, 0) / 1.0, 1.0) — maps [-0.5, 0.5] to [0, 1]."""
    return min(max(trends.growth_velocity_30d + 0.5, 0.0) / 1.0, 1.0)


def _normalize_incident_severity(triage_report: TriageReport) -> float:
    """1 - (critical * 0.3 + warning * 0.1) clamped to [0, 1]."""
    penalty = triage_report.critical_count * 0.3 + triage_report.warning_count * 0.1
    return max(0.0, min(1.0, 1.0 - penalty))


def compute_health_score(
    metrics: AnalyticsMetrics | None,
    trends: TrendAnalysis | None,
    triage_report: TriageReport | None,
    tracks: list[TrackData] | None,
) -> HealthScoreResult:
    """Compute composite health score from available data."""
    components: dict[str, float | None] = {}
    missing: list[str] = []

    # Engagement rate — needs metrics
    if metrics is not None:
        components["engagement_rate"] = _normalize_engagement_rate(metrics)
    else:
        components["engagement_rate"] = None
        missing.append("engagement_rate")

    # Catalog diversity — needs metrics
    if metrics is not None:
        components["catalog_diversity"] = _normalize_catalog_diversity(metrics)
    else:
        components["catalog_diversity"] = None
        missing.append("catalog_diversity")

    # Release cadence — needs tracks with created_at
    if tracks is not None and any(t.created_at is not None for t in tracks):
        components["release_cadence"] = _normalize_release_cadence(tracks)
    else:
        components["release_cadence"] = None
        missing.append("release_cadence")

    # Trend momentum — needs trends
    if trends is not None:
        components["trend_momentum"] = _normalize_trend_momentum(trends)
    else:
        components["trend_momentum"] = None
        missing.append("trend_momentum")

    # Incident severity — needs triage report
    if triage_report is not None:
        components["incident_severity"] = _normalize_incident_severity(triage_report)
    else:
        components["incident_severity"] = None
        missing.append("incident_severity")

    # Compute weighted score from available components
    numerator = 0.0
    denominator = 0.0
    for name, value in components.items():
        if value is not None:
            numerator += value * WEIGHTS[name]
            denominator += WEIGHTS[name]

    if denominator == 0.0:
        score = 0
    else:
        score = round(numerator / denominator * 100)

    # Clamp to [0, 100]
    score = max(0, min(100, score))

    return HealthScoreResult(
        score=score,
        components=components,
        missing_components=missing,
    )


def is_significant_change(previous_score: int, current_score: int) -> bool:
    """Flag health score changes > 10 points as significant."""
    return abs(current_score - previous_score) > 10
