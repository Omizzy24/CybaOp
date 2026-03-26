"""Tests for LangGraph edge routing logic."""

from src.agent.edges.routing import (
    route_after_fetch,
    route_after_metrics,
    route_by_tier,
    route_after_trends,
)


def _make_state(**overrides):
    base = {
        "user_id": "u1",
        "soundcloud_token": "tok",
        "correlation_id": "corr",
        "tier": "free",
        "profile_data": None,
        "tracks_data": None,
        "metrics": None,
        "trends": None,
        "insights": [],
        "final_report": None,
        "nodes_executed": [],
        "error": None,
        "snapshots": [],
    }
    base.update(overrides)
    return base


def test_route_after_fetch_success():
    assert route_after_fetch(_make_state()) == "fetch_tracks"


def test_route_after_fetch_error():
    assert route_after_fetch(_make_state(error="API down")) == "format_report"


def test_route_by_tier_free():
    # Free tier now gets calculate_metrics (catalog overview)
    assert route_by_tier(_make_state(tier="free")) == "calculate_metrics"


def test_route_by_tier_pro():
    assert route_by_tier(_make_state(tier="pro")) == "calculate_metrics"


def test_route_by_tier_enterprise():
    assert route_by_tier(_make_state(tier="enterprise")) == "calculate_metrics"


def test_route_by_tier_error_overrides():
    assert route_by_tier(_make_state(tier="pro", error="fail")) == "format_report"


def test_route_after_metrics_free():
    # Free tier: metrics → format_report (skip trends/insights)
    assert route_after_metrics(_make_state(tier="free")) == "format_report"


def test_route_after_metrics_pro():
    # Pro tier: metrics → detect_trends
    assert route_after_metrics(_make_state(tier="pro")) == "detect_trends"


def test_route_after_metrics_error():
    assert route_after_metrics(_make_state(error="fail")) == "format_report"


def test_route_after_trends_success():
    assert route_after_trends(_make_state()) == "generate_insights"


def test_route_after_trends_error():
    assert route_after_trends(_make_state(error="fail")) == "format_report"
