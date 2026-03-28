"""Auth routes — SoundCloud OAuth token exchange + user profile."""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse

from src.api.auth import create_jwt, get_current_user
from src.shared.config import get_settings
from src.shared.logging import get_logger
from src.shared.models import AuthTokenRequest, AuthTokenResponse, Tier
from src.tools.soundcloud import exchange_code_for_token, fetch_profile
from pydantic import BaseModel

logger = get_logger("routes.auth")
router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/token", response_model=AuthTokenResponse)
async def exchange_token(request: AuthTokenRequest):
    """Exchange SoundCloud OAuth code for a CybaOp JWT.

    This is the single point of token exchange. The frontend sends the
    authorization code here; the backend handles everything: SoundCloud
    token exchange, profile fetch, user persistence, JWT issuance.
    """
    settings = get_settings()

    # 1. Exchange code for SoundCloud access token
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

    # 2. Fetch profile to populate user record + JWT claims
    try:
        profile = await fetch_profile(sc_token)
    except Exception as e:
        logger.error("profile_fetch_after_auth_failed", error=str(e))
        raise HTTPException(status_code=502, detail=f"Failed to fetch SoundCloud profile: {e}")

    # 3. Persist user to DB (graceful skip in dev when Postgres is unavailable)
    user_id = f"sc_{profile.platform_user_id}"
    try:
        from src.db.queries import upsert_user

        user_id = await upsert_user(
            soundcloud_user_id=profile.platform_user_id,
            username=profile.username,
            display_name=profile.display_name,
            soundcloud_token=sc_token,
            avatar_url=profile.avatar_url,
        )
    except Exception as e:
        if settings.env == "development":
            logger.warning("db_unavailable_skipping_persist", error=str(e))
        else:
            logger.error("user_upsert_failed", error=str(e))
            raise HTTPException(status_code=503, detail="Database error during user creation")

    # 4. Issue JWT — this is the only token the frontend stores
    # Read tier from DB (may have been upgraded previously)
    tier = "free"
    try:
        from src.db.queries import get_user
        db_user = await get_user(user_id)
        if db_user:
            tier = db_user.get("tier", "free")
    except Exception:
        pass

    jwt_token = create_jwt(user_id=user_id, username=profile.username, tier=tier)

    logger.info("auth_complete", user_id=user_id, username=profile.username, tier=tier)

    return AuthTokenResponse(
        access_token=jwt_token,
        user_id=user_id,
        username=profile.username,
        tier=Tier(tier),
    )


@router.get("/me")
async def get_me(user: dict = Depends(get_current_user)):
    """Return the authenticated user's profile.

    In dev without DB: returns JWT claims only (username, tier).
    With DB: fetches full profile from SoundCloud using stored token.
    """
    settings = get_settings()
    user_id = user["sub"]
    username = user.get("username", "")
    tier = user.get("tier", "free")

    # Try to get the full profile from DB + SoundCloud
    try:
        from src.db.queries import get_user, get_user_token

        db_user = await get_user(user_id)
        if db_user:
            sc_token = db_user.get("soundcloud_token")
            if sc_token:
                try:
                    profile = await fetch_profile(sc_token)
                    return {
                        "user_id": user_id,
                        "username": profile.username,
                        "display_name": profile.display_name,
                        "followers_count": profile.followers_count,
                        "following_count": profile.following_count,
                        "track_count": profile.track_count,
                        "playlist_count": profile.playlist_count,
                        "likes_count": profile.likes_count,
                        "avatar_url": profile.avatar_url,
                        "profile_url": profile.profile_url,
                        "tier": db_user.get("tier", tier),
                    }
                except Exception as e:
                    logger.warning("profile_fetch_failed_using_cached", error=str(e))
                    # Fall through to return DB-cached data
            return {
                "user_id": user_id,
                "username": db_user.get("username", username),
                "display_name": db_user.get("display_name", ""),
                "avatar_url": db_user.get("avatar_url", ""),
                "tier": db_user.get("tier", tier),
            }
    except Exception as e:
        if settings.env != "development":
            logger.error("db_error_in_get_me", error=str(e))
        # In dev without DB, fall through to JWT-only response

    # Minimal response from JWT claims when DB is unavailable
    return {
        "user_id": user_id,
        "username": username,
        "tier": tier,
    }



@router.post("/logout")
async def logout(user: dict = Depends(get_current_user)):
    """Log out the current user.

    Currently stateless (JWT-based), so this is a no-op on the backend.
    The frontend clears the cookie. When we add a token blacklist or
    refresh token rotation, revocation logic goes here.
    """
    logger.info("user_logout", user_id=user["sub"])
    return JSONResponse({"success": True})


class SCTokenRequest(BaseModel):
    access_token: str


@router.post("/token-from-sc", response_model=AuthTokenResponse)
async def register_sc_token(request: SCTokenRequest):
    """Accept an already-exchanged SoundCloud token, fetch profile, persist, issue JWT.

    Used when the frontend exchanges the OAuth code directly with SoundCloud
    (to avoid cold-start latency killing the short-lived code), then sends
    the resulting SC token here for user registration and JWT issuance.
    """
    settings = get_settings()
    sc_token = request.access_token

    try:
        profile = await fetch_profile(sc_token)
    except Exception as e:
        logger.error("profile_fetch_failed", error=str(e))
        raise HTTPException(status_code=502, detail=f"Failed to fetch SoundCloud profile: {e}")

    user_id = f"sc_{profile.platform_user_id}"
    try:
        from src.db.queries import upsert_user
        user_id = await upsert_user(
            soundcloud_user_id=profile.platform_user_id,
            username=profile.username,
            display_name=profile.display_name,
            soundcloud_token=sc_token,
            avatar_url=profile.avatar_url,
        )
    except Exception as e:
        if settings.env == "development":
            logger.warning("db_unavailable_skipping_persist", error=str(e))
        else:
            logger.error("user_upsert_failed", error=str(e))
            raise HTTPException(status_code=503, detail="Database error")

    jwt_token = create_jwt(user_id=user_id, username=profile.username)
    logger.info("auth_complete_from_sc_token", user_id=user_id, username=profile.username)

    return AuthTokenResponse(
        access_token=jwt_token,
        user_id=user_id,
        username=profile.username,
        tier=Tier.FREE,
    )
