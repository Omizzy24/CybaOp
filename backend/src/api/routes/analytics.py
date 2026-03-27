"""Analytics routes — the core product endpoints."""

import json
import time
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query

from src.agent.graph import build_analytics_graph
from src.api.auth import get_current_user
from src.db.queries import get_user_token, update_last_analytics, save_track_snapshots, get_all_track_history, get_plays_over_time
from src.shared.config import get_settings
from src.shared.logging import bind_correlation_id, get_logger
from src.shared.models import AnalyticsResponse, HistoryResponse, HistoryDataPoint

logger = get_logger("routes.analytics")
router = APIRouter(prefix="/analytics", tags=["analytics"])

# In-memory cache: user_id → (timestamp, response_json)
_cache: dict[str, tuple[float, dict]] = {}


def _get_cached(user_id: str, ttl: int) -> dict | None:
    """Return cached response if fresh, else None."""
    entry = _cache.get(user_id)
    if not entry:
        return None
    cached_at, data = entry
    if time.time() - cached_at > ttl:
        del _cache[user_id]
        return None
    return data


def _set_cache(user_id: str, data: dict) -> None:
    """Cache a response. Evict oldest if cache grows too large."""
    if len(_cache) > 500:
        oldest_key = min(_cache, key=lambda k: _cache[k][0])
        del _cache[oldest_key]
    _cache[user_id] = (time.time(), data)


@router.get("/insights", response_model=AnalyticsResponse)
async def get_insights(
    user: dict = Depends(get_current_user),
    force_refresh: bool = Query(False),
):
    """Run the full analytics pipeline for the authenticated user.

    Results are cached for cache_ttl_tracks seconds (default 30 min).
    Pass ?force_refresh=true to bypass cache.
    """
    correlation_id = str(uuid.uuid4())
    bind_correlation_id(correlation_id)
    start = time.time()

    user_id = user["sub"]
    tier = user.get("tier", "free")
    settings = get_settings()

    logger.info("analytics_request", user_id=user_id, tier=tier)

    # Check cache first (unless force_refresh)
    if not force_refresh:
        cached = _get_cached(user_id, settings.cache_ttl_tracks)
        if cached:
            elapsed = int((time.time() - start) * 1000)
            logger.info("analytics_cache_hit", user_id=user_id, elapsed_ms=elapsed)
            cached["request_id"] = correlation_id
            cached["processing_time_ms"] = elapsed
            cached["message"] = "Analytics loaded from cache"
            return AnalyticsResponse(**cached)

    # Get SoundCloud token from DB
    token = await get_user_token(user_id)
    if not token:
        raise HTTPException(
            status_code=401,
            detail="SoundCloud token not found — re-authenticate",
        )

    # Build and run the analytics graph
    try:
        graph = build_analytics_graph()

        # Load historical snapshots for trend detection
        try:
            snapshots = await get_all_track_history(user_id)
        except Exception:
            snapshots = []

        initial_state = {
            "user_id": user_id,
            "soundcloud_token": token,
            "correlation_id": correlation_id,
            "tier": tier,
            "profile_data": None,
            "tracks_data": None,
            "metrics": None,
            "trends": None,
            "insights": [],
            "final_report": None,
            "nodes_executed": [],
            "error": None,
            "snapshots": snapshots,
            "eras": [],
            "era_fingerprint": None,
        }

        result = await graph.ainvoke(initial_state)
        elapsed = int((time.time() - start) * 1000)

        report = result.get("final_report")
        if report:
            report.processing_time_ms = elapsed

        # Persist track snapshots for trend detection (non-fatal)
        tracks_data = result.get("tracks_data") or []
        if tracks_data:
            try:
                snapshot_records = [
                    {
                        "track_id": t.platform_track_id,
                        "title": t.title,
                        "play_count": t.play_count,
                        "like_count": t.like_count,
                        "comment_count": t.comment_count,
                        "repost_count": t.repost_count,
                    }
                    for t in tracks_data
                ]
                await save_track_snapshots(user_id, snapshot_records)
            except Exception as e:
                logger.warning("snapshot_save_failed", user_id=user_id, error=str(e))

        await update_last_analytics(user_id)

        response = AnalyticsResponse(
            request_id=correlation_id,
            success=True,
            message="Analytics generated successfully",
            report=report,
            processing_time_ms=elapsed,
        )

        # Cache the result
        _set_cache(user_id, response.model_dump())

        logger.info(
            "analytics_complete",
            user_id=user_id,
            elapsed_ms=elapsed,
            nodes=result.get("nodes_executed", []),
        )

        return response

    except Exception as e:
        elapsed = int((time.time() - start) * 1000)
        logger.error("analytics_failed", user_id=user_id, error=str(e))
        return AnalyticsResponse(
            request_id=correlation_id,
            success=False,
            message=f"Analytics error: {str(e)}",
            error_code="INTERNAL_ERROR",
            processing_time_ms=elapsed,
        )


@router.get("/history", response_model=HistoryResponse)
async def get_history(
    user: dict = Depends(get_current_user),
    days: int = Query(90, ge=1, le=365),
):
    """Return daily aggregate play/like counts for the plays-over-time chart."""
    user_id = user["sub"]
    logger.info("history_request", user_id=user_id, days=days)

    try:
        rows = await get_plays_over_time(user_id, days)
        data = [
            HistoryDataPoint(
                day=str(r["day"]),
                total_plays=r["total_plays"],
                total_likes=r["total_likes"],
                track_count=r["track_count"],
            )
            for r in rows
        ]
        return HistoryResponse(
            success=True,
            data=data,
            days_requested=days,
            message=f"{len(data)} data points",
        )
    except Exception as e:
        logger.error("history_failed", user_id=user_id, error=str(e))
        return HistoryResponse(
            success=False,
            message=f"Failed to load history: {str(e)}",
            days_requested=days,
        )
