"""Billing routes — Stripe integration for Pro tier upgrades."""

import time

from fastapi import APIRouter, Depends, HTTPException, Request

from src.api.auth import get_current_user, create_jwt
from src.db.queries import get_user, upgrade_user_tier
from src.shared.config import get_settings
from src.shared.logging import get_logger
from src.shared.models import ErrorResponse

logger = get_logger("routes.billing")
router = APIRouter(prefix="/billing", tags=["billing"])


@router.get("/status")
async def billing_status(user: dict = Depends(get_current_user)):
    """Return the user's current tier and Pro feature access."""
    user_id = user["sub"]
    tier = user.get("tier", "free")

    return {
        "tier": tier,
        "is_pro": tier in ("pro", "enterprise"),
        "features": _tier_features(tier),
    }


@router.post("/upgrade")
async def upgrade_to_pro(
    request: Request,
    user: dict = Depends(get_current_user),
):
    """Upgrade user to Pro tier.

    In production this would verify a Stripe payment intent.
    For now, accepts a simple upgrade request for demo/beta purposes.
    """
    user_id = user["sub"]
    username = user.get("username", "")
    settings = get_settings()

    logger.info("upgrade_request", user_id=user_id)

    try:
        await upgrade_user_tier(user_id, "pro")
    except Exception as e:
        logger.error("upgrade_failed", user_id=user_id, error=str(e))
        raise HTTPException(status_code=500, detail="Upgrade failed")

    # Issue a new JWT with the updated tier
    new_token = create_jwt(user_id, username, tier="pro")

    logger.info("upgrade_complete", user_id=user_id, tier="pro")

    return {
        "success": True,
        "tier": "pro",
        "token": new_token,
        "features": _tier_features("pro"),
    }


@router.post("/webhook")
async def stripe_webhook(request: Request):
    """Stripe webhook endpoint — placeholder for production integration.

    In production:
    1. Verify the Stripe signature
    2. Handle checkout.session.completed → upgrade tier
    3. Handle customer.subscription.deleted → downgrade tier
    """
    settings = get_settings()
    body = await request.body()

    logger.info("stripe_webhook_received", body_length=len(body))

    # Placeholder — in production, verify stripe signature and process events
    return {"received": True}


def _tier_features(tier: str) -> dict:
    """Return feature flags for a given tier."""
    base = {
        "analytics_basic": True,
        "engagement_metrics": True,
        "catalog_health": True,
        "release_timing": True,
        "era_timeline": True,
        "plays_history": True,
        "share_card": True,
    }

    pro = {
        "ai_insights": True,
        "growth_velocity": True,
        "trend_detection": True,
        "anomaly_alerts": True,
        "engagement_decay": True,
        "unlimited_history": True,
        "priority_refresh": True,
    }

    if tier in ("pro", "enterprise"):
        return {**base, **pro}
    return {**base, **{k: False for k in pro}}
