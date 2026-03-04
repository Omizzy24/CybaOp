"""Detect trends node — moving averages, growth velocity, peak periods."""

from src.agent.state import AnalyticsState
from src.shared.logging import get_logger
from src.tools.trends import analyze_trends

logger = get_logger("node.detect_trends")


def detect_trends_node(state: AnalyticsState) -> dict:
    """Run trend analysis on the catalog."""
    try:
        tracks = state.get("tracks_data") or []
        snapshots = state.get("snapshots") or []

        if not tracks:
            logger.warning("no_tracks_for_trends")
            return {
                "nodes_executed": state.get("nodes_executed", []) + ["detect_trends"],
            }

        trends = analyze_trends(tracks, snapshots if snapshots else None)

        logger.info(
            "trends_detected",
            gv_7d=trends.growth_velocity_7d,
            gv_30d=trends.growth_velocity_30d,
            best_day=trends.best_release_day,
            confidence=trends.confidence,
        )

        return {
            "trends": trends,
            "nodes_executed": state.get("nodes_executed", []) + ["detect_trends"],
        }
    except Exception as e:
        logger.error("detect_trends_failed", error=str(e))
        return {
            "nodes_executed": state.get("nodes_executed", []) + ["detect_trends"],
            "error": str(e),
        }
