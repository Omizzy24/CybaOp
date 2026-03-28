"""JWT utilities for auth between Next.js frontend and FastAPI backend."""

from datetime import datetime, timedelta, timezone

import jwt
from fastapi import HTTPException, Request

from src.shared.config import get_settings
from src.shared.errors import TierRestrictionError
from src.shared.logging import get_logger

logger = get_logger("auth")


def create_jwt(user_id: str, username: str, tier: str = "free") -> str:
    """Create a JWT token for the authenticated user."""
    settings = get_settings()
    payload = {
        "sub": user_id,
        "username": username,
        "tier": tier,
        "iat": datetime.now(timezone.utc),
        "exp": datetime.now(timezone.utc) + timedelta(hours=settings.jwt_expiry_hours),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_jwt(token: str) -> dict:
    """Decode and validate a JWT token."""
    settings = get_settings()
    try:
        return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


def get_current_user(request: Request) -> dict:
    """Extract user from Authorization header. Returns JWT payload."""
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")
    token = auth_header[7:]
    return decode_jwt(token)


def require_pro(request: Request) -> dict:
    """Require Pro tier for workflow endpoints. Returns JWT payload."""
    user = get_current_user(request)
    tier = user.get("tier", "free")
    if tier not in ("pro", "enterprise"):
        raise TierRestrictionError("This feature requires a Pro subscription")
    return user
