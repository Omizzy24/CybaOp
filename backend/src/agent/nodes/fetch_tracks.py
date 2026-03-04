"""Fetch tracks node — full catalog with pagination, save snapshots."""

from src.agent.state import AnalyticsState
from src.db.queries import get_all_track_history, save_track_snapshots
from src.shared.logging import get_logger
from src.tools.soundcloud import fetch_tracks

logger = get_logger("node.fetch_tracks")


async def fetch_tracks_node(state: AnalyticsState) -> dict:
    """Fetch all tracks and save snapshots for trend tracking."""
    try:
        token = state["soundcloud_token"]
        user_id = state["user_id"]
        tracks = await fetch_tracks(token)

        # Save snapshots for historical trend detection
        snapshot_records = [
            {
                "track_id": t.platform_track_id,
                "title": t.title,
                "play_count": t.play_count,
                "like_count": t.like_count,
                "comment_count": t.comment_count,
                "repost_count": t.repost_count,
            }
            for t in tracks
        ]

        try:
            await save_track_snapshots(user_id, snapshot_records)
        except Exception as snap_err:
            logger.warning("snapshot_save_failed", error=str(snap_err))

        # Load historical snapshots for trend detection
        snapshots = []
        try:
            snapshots = await get_all_track_history(user_id)
        except Exception as hist_err:
            logger.warning("history_load_failed", error=str(hist_err))

        logger.info("tracks_fetched", count=len(tracks))

        return {
            "tracks_data": tracks,
            "snapshots": snapshots,
            "nodes_executed": state.get("nodes_executed", []) + ["fetch_tracks"],
        }
    except Exception as e:
        logger.error("fetch_tracks_failed", error=str(e))
        return {
            "tracks_data": [],
            "snapshots": [],
            "nodes_executed": state.get("nodes_executed", []) + ["fetch_tracks"],
            "error": str(e),
        }
