"""Triage routes — production-style incident detection for catalogs."""

import time

from fastapi import APIRouter, Depends

from src.api.auth import get_current_user
from src.db.queries import get_user_token, get_all_track_history
from src.shared.logging import get_logger
from src.tools.soundcloud import fetch_tracks
from src.tools.triage import run_triage

logger = get_logger("routes.triage")
router = APIRouter(prefix="/triage", tags=["triage"])


@router.get("")
async def get_triage(user: dict = Depends(get_current_user)):
    """Run triage on the user's catalog. Returns incidents sorted by severity."""
    user_id = user["sub"]
    start = time.time()

    logger.info("triage_request", user_id=user_id)

    token = await get_user_token(user_id)
    if not token:
        return {"success": False, "message": "SoundCloud token not found — re-authenticate"}

    try:
        tracks = await fetch_tracks(token)
    except Exception as e:
        logger.error("triage_fetch_failed", user_id=user_id, error=str(e))
        return {"success": False, "message": f"Failed to fetch tracks: {e}"}

    # Load snapshots for decay detection
    snapshots = []
    try:
        snapshots = await get_all_track_history(user_id)
    except Exception:
        pass

    report = run_triage(tracks, snapshots)
    elapsed = int((time.time() - start) * 1000)

    logger.info("triage_complete", user_id=user_id, incidents=report.incident_count, elapsed_ms=elapsed)

    return {
        "success": True,
        "triage": report.model_dump(),
        "processing_time_ms": elapsed,
    }
