"""Billing routes — Stripe integration for Pro tier upgrades."""

import stripe
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse

from src.api.auth import get_current_user, create_jwt
from src.db.queries import (
    get_user,
    get_user_by_stripe_customer,
    get_user_by_stripe_subscription,
    update_user_stripe_info,
)
from src.shared.config import get_settings
from src.shared.errors import StripeError, TierRestrictionError, ValidationError
from src.shared.logging import get_logger
from src.shared.models import BillingStatusResponse, CheckoutResponse, PortalResponse

logger = get_logger("routes.billing")
router = APIRouter(prefix="/billing", tags=["billing"])


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


def maybe_refresh_jwt(user_jwt: dict, db_user: dict) -> str | None:
    """If JWT tier differs from DB tier, return a new JWT. Otherwise None."""
    if user_jwt.get("tier") != db_user.get("tier"):
        return create_jwt(db_user["id"], db_user.get("username", ""), db_user["tier"])
    return None


@router.get("/status")
async def billing_status(user: dict = Depends(get_current_user)):
    """Return the user's current tier, subscription state, and Pro feature access."""
    user_id = user["sub"]
    db_user = await get_user(user_id)
    tier = db_user.get("tier", "free") if db_user else user.get("tier", "free")
    is_pro = tier in ("pro", "enterprise")
    sub_status = db_user.get("subscription_status") if db_user else None
    ends_at = db_user.get("subscription_ends_at") if db_user else None
    warning = "Your payment method needs updating" if sub_status == "past_due" else None

    response_data = BillingStatusResponse(
        tier=tier,
        is_pro=is_pro,
        features=_tier_features(tier),
        subscription_status=sub_status,
        subscription_ends_at=ends_at.isoformat() if ends_at else None,
        warning=warning,
    )

    response = JSONResponse(content=response_data.model_dump())
    if db_user:
        new_token = maybe_refresh_jwt(user, db_user)
        if new_token:
            response.headers["X-Refreshed-Token"] = new_token
    return response


@router.post("/checkout")
async def create_checkout(user: dict = Depends(get_current_user)):
    """Create a Stripe Checkout Session for Pro subscription."""
    settings = get_settings()
    if not settings.stripe_secret_key or not settings.stripe_pro_price_id:
        raise StripeError("Billing is not configured. Contact support.")

    user_id = user["sub"]
    db_user = await get_user(user_id)

    if db_user and db_user.get("subscription_status") == "active":
        raise ValidationError("You already have an active Pro subscription.")

    stripe.api_key = settings.stripe_secret_key

    # Get or create Stripe Customer
    customer_id = db_user.get("stripe_customer_id") if db_user else None
    if not customer_id:
        try:
            customer = stripe.Customer.create(
                metadata={"user_id": user_id},
            )
            customer_id = customer.id
            await update_user_stripe_info(user_id, stripe_customer_id=customer_id)
        except stripe.error.StripeError as e:
            raise StripeError(f"Payment service temporarily unavailable: {e}")

    # Create Checkout Session
    try:
        session = stripe.checkout.Session.create(
            customer=customer_id,
            mode="subscription",
            line_items=[{"price": settings.stripe_pro_price_id, "quantity": 1}],
            success_url=f"{settings.frontend_url}/dashboard/pro?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{settings.frontend_url}/dashboard/pro",
            metadata={"user_id": user_id},
        )
    except stripe.error.StripeError as e:
        raise StripeError(f"Payment service temporarily unavailable: {e}")

    logger.info("checkout_session_created", user_id=user_id, session_id=session.id)
    return CheckoutResponse(url=session.url)


@router.post("/portal")
async def create_portal(user: dict = Depends(get_current_user)):
    """Create a Stripe Customer Portal session."""
    settings = get_settings()
    if not settings.stripe_secret_key:
        raise StripeError("Billing is not configured. Contact support.")

    user_id = user["sub"]
    db_user = await get_user(user_id)

    customer_id = db_user.get("stripe_customer_id") if db_user else None
    if not customer_id:
        raise ValidationError("No subscription found. Use checkout to subscribe.")

    tier = db_user.get("tier", "free") if db_user else "free"
    if tier not in ("pro", "enterprise"):
        raise TierRestrictionError("Portal access requires an active Pro subscription.")

    stripe.api_key = settings.stripe_secret_key
    try:
        session = stripe.billing_portal.Session.create(
            customer=customer_id,
            return_url=f"{settings.frontend_url}/dashboard/pro",
        )
    except stripe.error.StripeError as e:
        raise StripeError(f"Subscription management temporarily unavailable: {e}")

    logger.info("portal_session_created", user_id=user_id)
    return PortalResponse(url=session.url)


@router.post("/webhook")
async def stripe_webhook(request: Request):
    """Process Stripe webhook events with signature verification."""
    settings = get_settings()
    if not settings.stripe_webhook_secret:
        logger.warning("stripe_webhook_secret_not_configured")
        return JSONResponse({"received": True})

    body = await request.body()
    sig = request.headers.get("Stripe-Signature")
    if not sig:
        return JSONResponse({"error": "Missing Stripe-Signature"}, status_code=400)

    try:
        event = stripe.Webhook.construct_event(body, sig, settings.stripe_webhook_secret)
    except stripe.error.SignatureVerificationError:
        logger.warning("stripe_webhook_signature_invalid")
        return JSONResponse({"error": "Invalid signature"}, status_code=400)
    except Exception as e:
        logger.error("stripe_webhook_construct_failed", error=str(e))
        return JSONResponse({"error": "Invalid payload"}, status_code=400)

    event_type = event["type"]
    logger.info("stripe_webhook_received", event_type=event_type, event_id=event["id"])

    try:
        if event_type == "checkout.session.completed":
            await _handle_checkout_completed(event["data"]["object"])
        elif event_type == "customer.subscription.updated":
            await _handle_subscription_updated(event["data"]["object"])
        elif event_type == "customer.subscription.deleted":
            await _handle_subscription_deleted(event["data"]["object"])
        elif event_type == "invoice.payment_failed":
            await _handle_payment_failed(event["data"]["object"])
        else:
            logger.info("stripe_webhook_ignored", event_type=event_type)
    except Exception as e:
        logger.error("stripe_webhook_processing_error", event_type=event_type, error=str(e))

    return JSONResponse({"received": True})


async def _handle_checkout_completed(session_obj: dict) -> None:
    """Handle checkout.session.completed — upgrade user to Pro."""
    user_id = session_obj.get("metadata", {}).get("user_id")
    if not user_id:
        logger.error("checkout_completed_missing_user_id", session_id=session_obj.get("id"))
        return

    db_user = await get_user(user_id)
    if not db_user:
        logger.error("checkout_completed_user_not_found", user_id=user_id)
        return

    sub_id = session_obj.get("subscription")
    # Idempotency: skip if already active with same subscription
    if db_user.get("subscription_status") == "active" and db_user.get("stripe_subscription_id") == sub_id:
        logger.info("checkout_completed_idempotent_skip", user_id=user_id)
        return

    await update_user_stripe_info(
        user_id,
        stripe_subscription_id=sub_id,
        subscription_status="active",
        tier="pro",
    )
    logger.info("user_upgraded_via_checkout", user_id=user_id, subscription_id=sub_id)


async def _handle_subscription_updated(sub_obj: dict) -> None:
    """Handle customer.subscription.updated — sync subscription status."""
    sub_id = sub_obj.get("id")
    db_user = await get_user_by_stripe_subscription(sub_id)
    if not db_user:
        logger.warning("subscription_updated_user_not_found", subscription_id=sub_id)
        return

    new_status = sub_obj.get("status")  # active, past_due, canceled, etc.
    await update_user_stripe_info(db_user["id"], subscription_status=new_status)
    logger.info("subscription_status_updated", user_id=db_user["id"], status=new_status)


async def _handle_subscription_deleted(sub_obj: dict) -> None:
    """Handle customer.subscription.deleted — downgrade user to free."""
    sub_id = sub_obj.get("id")
    db_user = await get_user_by_stripe_subscription(sub_id)
    if not db_user:
        # Try by customer ID as fallback
        customer_id = sub_obj.get("customer")
        if customer_id:
            db_user = await get_user_by_stripe_customer(customer_id)

    if not db_user:
        logger.warning("subscription_deleted_user_not_found", subscription_id=sub_id)
        return

    # Idempotency: skip if already free
    if db_user.get("tier") == "free":
        logger.info("subscription_deleted_idempotent_skip", user_id=db_user["id"])
        return

    period_end = sub_obj.get("current_period_end")
    ends_at = datetime.fromtimestamp(period_end, tz=timezone.utc) if period_end else None

    await update_user_stripe_info(
        db_user["id"],
        tier="free",
        subscription_status="canceled",
        stripe_subscription_id="",  # clear
        subscription_ends_at=ends_at,
    )
    logger.info("user_downgraded_via_deletion", user_id=db_user["id"])


async def _handle_payment_failed(invoice_obj: dict) -> None:
    """Handle invoice.payment_failed — flag account as past_due."""
    customer_id = invoice_obj.get("customer")
    if not customer_id:
        logger.warning("payment_failed_missing_customer")
        return

    db_user = await get_user_by_stripe_customer(customer_id)
    if not db_user:
        logger.warning("payment_failed_user_not_found", customer_id=customer_id)
        return

    await update_user_stripe_info(db_user["id"], subscription_status="past_due")
    logger.info(
        "payment_failed_flagged",
        user_id=db_user["id"],
        invoice_id=invoice_obj.get("id"),
    )


@router.post("/upgrade")
async def upgrade_to_pro(user: dict = Depends(get_current_user)):
    """Deprecated — use POST /billing/checkout instead."""
    return JSONResponse(
        status_code=410,
        content={
            "success": False,
            "message": "This endpoint has been deprecated. Use POST /billing/checkout to start a Stripe subscription.",
        },
    )
