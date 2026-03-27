"""Analytics pipeline state definition for LangGraph."""

from typing import Optional, TypedDict

from src.shared.models import (
    AnalyticsMetrics,
    AnalyticsReport,
    InsightItem,
    ProfileData,
    TrackData,
    TrendAnalysis,
)


class AnalyticsState(TypedDict):
    user_id: str
    soundcloud_token: str
    correlation_id: str
    tier: str  # "free", "pro", "enterprise"
    profile_data: Optional[ProfileData]
    tracks_data: Optional[list[TrackData]]
    metrics: Optional[AnalyticsMetrics]
    trends: Optional[TrendAnalysis]
    insights: list[InsightItem]
    final_report: Optional[AnalyticsReport]
    nodes_executed: list[str]
    error: Optional[str]
    snapshots: list[dict]  # historical track snapshots for trend detection
    eras: list[dict]
    era_fingerprint: Optional[dict]
