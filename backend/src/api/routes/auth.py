"""Auth routes — SoundCloud OAuth token exchange."""

from fastapi import APIRouter, HTTPException

from src.api.auth import create_jwt
from src.db.queries import upsert_user
from src.shared.config import get_settings
from src.shared.logging import get_logger
from src.shared.models import AuthTokenRequest, AuthTokenResponse, Tier
from src.tools.soundcloud import exchange_code_for_token, fetch_profile

logger = get_logger("routes.auth")
router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/token", response_model=AuthTokenResponse)
async def exchange_token(request: AuthTokenRequest):
    """Exchange SoundCloud OAuth code for a CybaOp JWT."""
    settings = get_settings()

    # Exchange code for SoundCloud access token
    try:
        token_data = await exchange_code_for_token(
            code=request.code,
            client_id=settings.soundcloud_client_id,
            client_secret=settings.soundcloud_client_secret,
            redirect_uri=request.redirect_uri,
        )
    except Exception as e:
        logger.error("token_exchange_failed", error=str(e))
        raise HTTPException(status_code=400, detail=f"Token exchange failed: {e}")

    sc_token = token_data.get("access_token")
    if not sc_token:
        raise HTTPException(status_code=400, detail="No access token in response")

    # Fetch profile to get user info
    try:
        profile = await fetch_profile(sc_token)
    except Exception as e:
        logger.error("profile_fetch_after_auth_failed", error=str(e))
        raise HTTPException(status_code=502, detail=f"Failed to fetch SoundCloud profile: {e}")

    # Upsert user in database
    try:
        user_id = await upsert_user(
            soundcloud_user_id=profile.platform_user_id,
            username=profile.username,
            display_name=profile.display_name,
            soundcloud_token=sc_token,
            avatar_url=profile.avatar_url,
        )
    except Exception as e:
        logger.error("user_upsert_failed", error=str(e))
        raise HTTPException(status_code=503, detail="Database error during user creation")

    # Create JWT
    jwt_token = create_jwt(user_id=user_id, username=profile.username)

    logger.info("auth_complete", user_id=user_id, username=profile.username)

    return AuthTokenResponse(
        access_token=jwt_token,
        user_id=user_id,
        username=profile.username,
        tier=Tier.FREE,
    )
