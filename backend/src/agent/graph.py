"""LangGraph StateGraph for the CybaOp analytics pipeline."""

from langgraph.graph import END, StateGraph

from src.agent.edges.routing import (
    route_after_fetch,
    route_after_trends,
    route_by_tier,
)
from src.agent.nodes.calculate_metrics import calculate_metrics_node
from src.agent.nodes.detect_trends import detect_trends_node
from src.agent.nodes.fetch_profile import fetch_profile_node
from src.agent.nodes.fetch_tracks import fetch_tracks_node
from src.agent.nodes.format_report import format_report_node
from src.agent.nodes.generate_insights import generate_insights_node
from src.agent.state import AnalyticsState


def build_analytics_graph() -> StateGraph:
    """Build and compile the analytics pipeline graph.

    Free tier:  fetch_profile → fetch_tracks → format_report
    Pro tier:   fetch_profile → fetch_tracks → calculate_metrics
                → detect_trends → generate_insights → format_report
    """
    graph = StateGraph(AnalyticsState)

    # Add nodes
    graph.add_node("fetch_profile", fetch_profile_node)
    graph.add_node("fetch_tracks", fetch_tracks_node)
    graph.add_node("calculate_metrics", calculate_metrics_node)
    graph.add_node("detect_trends", detect_trends_node)
    graph.add_node("generate_insights", generate_insights_node)
    graph.add_node("format_report", format_report_node)

    # Entry point
    graph.set_entry_point("fetch_profile")

    # fetch_profile → fetch_tracks (or format_report on error)
    graph.add_conditional_edges(
        "fetch_profile",
        route_after_fetch,
        {"fetch_tracks": "fetch_tracks", "format_report": "format_report"},
    )

    # fetch_tracks → tier-based routing
    graph.add_conditional_edges(
        "fetch_tracks",
        route_by_tier,
        {
            "calculate_metrics": "calculate_metrics",
            "format_report": "format_report",
        },
    )

    # calculate_metrics → detect_trends
    graph.add_edge("calculate_metrics", "detect_trends")

    # detect_trends → generate_insights (or format_report on error)
    graph.add_conditional_edges(
        "detect_trends",
        route_after_trends,
        {
            "generate_insights": "generate_insights",
            "format_report": "format_report",
        },
    )

    # generate_insights → format_report
    graph.add_edge("generate_insights", "format_report")

    # format_report → END
    graph.add_edge("format_report", END)

    return graph.compile()
