"""Fetch profile node — SoundCloud API call, normalize into ProfileData."""

from src.agent.state import AnalyticsState
from src.shared.logging import get_logger
from src.tools.soundcloud import fetch_profile

logger = get_logger("node.fetch_profile")


async def fetch_profile_node(state: AnalyticsState) -> dict:
    """Fetch the user's SoundCloud profile."""
    try:
        token = state["soundcloud_token"]
        profile = await fetch_profile(token)

        logger.info(
            "profile_fetched",
            username=profile.username,
            followers=profile.followers_count,
            tracks=profile.track_count,
        )

        return {
            "profile_data": profile,
            "nodes_executed": state.get("nodes_executed", []) + ["fetch_profile"],
        }
    except Exception as e:
        logger.error("fetch_profile_failed", error=str(e))
        return {
            "nodes_executed": state.get("nodes_executed", []) + ["fetch_profile"],
            "error": str(e),
        }
