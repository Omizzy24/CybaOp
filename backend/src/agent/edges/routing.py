"""Conditional edge functions for the analytics LangGraph pipeline."""

from src.agent.state import AnalyticsState


def route_after_fetch(state: AnalyticsState) -> str:
    """Route based on error state — if fetch failed, skip to format."""
    if state.get("error"):
        return "format_report"
    return "fetch_tracks"


def route_by_tier(state: AnalyticsState) -> str:
    """Route based on user tier after fetching tracks.
    All tiers get calculate_metrics now (free tier gets catalog overview).
    Pro/Enterprise continue to detect_trends and generate_insights."""
    if state.get("error"):
        return "format_report"
    return "calculate_metrics"


def route_after_metrics(state: AnalyticsState) -> str:
    """After metrics, free tier goes to format_report.
    Pro/Enterprise continue to detect_trends."""
    if state.get("error"):
        return "format_report"
    tier = state.get("tier", "free")
    if tier == "free":
        return "format_report"
    return "detect_trends"


def route_after_trends(state: AnalyticsState) -> str:
    """After trend detection, generate insights or skip to format."""
    if state.get("error"):
        return "format_report"
    return "generate_insights"
