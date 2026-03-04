"""Analytics routes — the core product endpoints."""

import time
import uuid

from fastapi import APIRouter, Depends, HTTPException

from src.agent.graph import build_analytics_graph
from src.api.auth import get_current_user
from src.db.queries import get_user_token, update_last_analytics
from src.shared.logging import bind_correlation_id, get_logger
from src.shared.models import AnalyticsResponse

logger = get_logger("routes.analytics")
router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/insights", response_model=AnalyticsResponse)
async def get_insights(user: dict = Depends(get_current_user)):
    """Run the full analytics pipeline for the authenticated user."""
    correlation_id = str(uuid.uuid4())
    bind_correlation_id(correlation_id)
    start = time.time()

    user_id = user["sub"]
    tier = user.get("tier", "free")

    logger.info("analytics_request", user_id=user_id, tier=tier)

    # Get SoundCloud token from DB
    token = await get_user_token(user_id)
    if not token:
        raise HTTPException(status_code=401, detail="SoundCloud token not found — re-authenticate")

    # Build and run the analytics graph
    try:
        graph = build_analytics_graph()
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
            "snapshots": [],
        }

        result = await graph.ainvoke(initial_state)
        elapsed = int((time.time() - start) * 1000)

        report = result.get("final_report")
        if report:
            report.processing_time_ms = elapsed

        await update_last_analytics(user_id)

        logger.info(
            "analytics_complete",
            user_id=user_id,
            elapsed_ms=elapsed,
            nodes=result.get("nodes_executed", []),
        )

        return AnalyticsResponse(
            request_id=correlation_id,
            success=True,
            message="Analytics generated successfully",
            report=report,
            processing_time_ms=elapsed,
        )

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
