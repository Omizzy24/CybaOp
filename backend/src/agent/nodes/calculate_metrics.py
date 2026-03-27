"""Calculate metrics node — pure math, no LLM."""

from src.agent.state import AnalyticsState
from src.shared.logging import get_logger
from src.shared.models import TrendAnalysis
from src.tools.engagement import compute_metrics
from src.tools.trends import detect_best_release_timing, detect_strongest_era, cluster_into_eras, fingerprint_era

logger = get_logger("node.calculate_metrics")


def calculate_metrics_node(state: AnalyticsState) -> dict:
    """Compute engagement rates, performance scores, catalog health, and release timing."""
    try:
        tracks = state.get("tracks_data") or []
        if not tracks:
            logger.warning("no_tracks_for_metrics")
            return {
                "nodes_executed": state.get("nodes_executed", []) + ["calculate_metrics"],
            }

        # Core engagement metrics (uses engagement.py)
        metrics = compute_metrics(tracks)

        # Release timing analysis (uses trends.py — available for all tiers)
        best_day, best_hour = detect_best_release_timing(tracks)
        era_start, era_end, era_desc = detect_strongest_era(tracks)

        # Build a minimal TrendAnalysis with release timing for free tier
        # Full trend analysis (growth velocity) requires snapshots and runs in detect_trends node
        trends = TrendAnalysis(
            best_release_day=best_day,
            best_release_hour=best_hour,
            strongest_era_start=era_start,
            strongest_era_end=era_end,
            strongest_era_description=era_desc,
            confidence=min(1.0, len(tracks) / 20.0),
        )

        logger.info(
            "metrics_computed",
            total_plays=metrics.total_plays,
            avg_engagement=metrics.avg_engagement_rate,
            concentration=metrics.catalog_concentration,
            best_release_day=best_day,
        )

        # Era clustering and fingerprinting
        eras = cluster_into_eras(tracks)
        era_fingerprint = None
        if eras:
            strongest = max(eras, key=lambda e: e["avg_engagement_rate"])
            era_tracks = [
                t for t in tracks
                if t.created_at and strongest["start"] <= t.created_at <= strongest["end"]
            ]
            if era_tracks:
                era_fingerprint = fingerprint_era(era_tracks)

        return {
            "metrics": metrics,
            "trends": trends,
            "eras": eras,
            "era_fingerprint": era_fingerprint,
            "nodes_executed": state.get("nodes_executed", []) + ["calculate_metrics"],
        }
    except Exception as e:
        logger.error("calculate_metrics_failed", error=str(e))
        return {
            "nodes_executed": state.get("nodes_executed", []) + ["calculate_metrics"],
            "error": str(e),
        }
