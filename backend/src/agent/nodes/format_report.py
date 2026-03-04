"""Format report node — assemble the final AnalyticsReport."""

from datetime import datetime, timezone

from src.agent.state import AnalyticsState
from src.shared.logging import get_logger
from src.shared.models import AnalyticsReport, ProfileData, Tier

logger = get_logger("node.format_report")


def format_report_node(state: AnalyticsState) -> dict:
    """Assemble the final analytics report."""
    try:
        error = state.get("error")
        profile = state.get("profile_data")
        tracks = state.get("tracks_data") or []
        metrics = state.get("metrics")
        trends = state.get("trends")
        insights = state.get("insights") or []
        nodes = state.get("nodes_executed", []) + ["format_report"]
        tier = Tier(state.get("tier", "free"))

        # If we have an error and no profile, return minimal report
        if error and not profile:
            report = AnalyticsReport(
                user_id=state["user_id"],
                profile=ProfileData(
                    platform_user_id="",
                    username="unknown",
                    display_name="Unknown",
                ),
                correlation_id=state.get("correlation_id", ""),
                nodes_executed=nodes,
                tier=tier,
            )

            return {"final_report": report, "nodes_executed": nodes}

        # Calculate data freshness
        freshness = 0
        is_stale = False
        if profile and profile.fetched_at:
            delta = (datetime.utcnow() - profile.fetched_at).total_seconds()
            freshness = int(delta)
            is_stale = freshness > 21600  # 6 hours

        top_tracks = metrics.top_tracks if metrics else []

        report = AnalyticsReport(
            user_id=state["user_id"],
            profile=profile,
            track_count=len(tracks),
            top_tracks=top_tracks[:10],
            metrics=metrics,
            trends=trends,
            insights=insights,
            tier=tier,
            data_freshness_seconds=freshness,
            is_stale=is_stale,
            correlation_id=state.get("correlation_id", ""),
            nodes_executed=nodes,
        )

        logger.info(
            "report_formatted",
            tier=tier.value,
            track_count=len(tracks),
            insights_count=len(insights),
            is_stale=is_stale,
        )

        return {"final_report": report, "nodes_executed": nodes}

    except Exception as e:
        logger.error("format_report_failed", error=str(e))
        report = AnalyticsReport(
            user_id=state.get("user_id", ""),
            profile=state.get("profile_data") or ProfileData(
                platform_user_id="", username="error", display_name="Error",
            ),
            correlation_id=state.get("correlation_id", ""),
            nodes_executed=state.get("nodes_executed", []) + ["format_report"],
        )
        return {"final_report": report, "nodes_executed": report.nodes_executed}
