"""Calculate metrics node — pure math, no LLM."""

from src.agent.state import AnalyticsState
from src.shared.logging import get_logger
from src.tools.engagement import compute_metrics

logger = get_logger("node.calculate_metrics")


def calculate_metrics_node(state: AnalyticsState) -> dict:
    """Compute engagement rates, performance scores, catalog health."""
    try:
        tracks = state.get("tracks_data") or []
        if not tracks:
            logger.warning("no_tracks_for_metrics")
            return {
                "nodes_executed": state.get("nodes_executed", []) + ["calculate_metrics"],
            }

        metrics = compute_metrics(tracks)

        logger.info(
            "metrics_computed",
            total_plays=metrics.total_plays,
            avg_engagement=metrics.avg_engagement_rate,
            concentration=metrics.catalog_concentration,
        )

        return {
            "metrics": metrics,
            "nodes_executed": state.get("nodes_executed", []) + ["calculate_metrics"],
        }
    except Exception as e:
        logger.error("calculate_metrics_failed", error=str(e))
        return {
            "nodes_executed": state.get("nodes_executed", []) + ["calculate_metrics"],
            "error": str(e),
        }
