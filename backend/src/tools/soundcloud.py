"""SoundCloud API wrapper — fetch + normalize into domain models."""

from datetime import datetime, timezone

import httpx

from src.shared.errors import QuotaExceededError, SoundCloudAPIError, TokenExpiredError
from src.shared.logging import get_logger
from src.shared.models import ProfileData, TrackData

logger = get_logger("tools.soundcloud")

SC_API_BASE = "https://api.soundcloud.com"


async def _sc_request(
    path: str, token: str, params: dict | None = None
) -> dict | list:
    """Make an authenticated SoundCloud API request."""
    headers = {"Authorization": f"OAuth {token}"}
    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.get(
            f"{SC_API_BASE}{path}",
            headers=headers,
            params=params or {},
        )

    if resp.status_code == 401:
        raise TokenExpiredError()
    if resp.status_code == 429:
        retry = int(resp.headers.get("Retry-After", "60"))
        raise QuotaExceededError(retry_after=retry)
    if resp.status_code >= 400:
        raise SoundCloudAPIError(
            f"SoundCloud API error: {resp.status_code}",
            status_code=resp.status_code,
        )
    return resp.json()


def _parse_datetime(val: str | None) -> datetime | None:
    """Parse SoundCloud datetime strings."""
    if not val:
        return None
    try:
        return datetime.fromisoformat(val.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        try:
            return datetime.strptime(val, "%Y/%m/%d %H:%M:%S %z")
        except (ValueError, AttributeError):
            return None


async def fetch_profile(token: str) -> ProfileData:
    """Fetch and normalize the authenticated user's profile."""
    data = await _sc_request("/me", token)
    logger.info("profile_fetched", username=data.get("permalink"))

    return ProfileData(
        platform_user_id=str(data.get("id", "")),
        username=data.get("permalink", ""),
        display_name=data.get("full_name") or data.get("username", ""),
        followers_count=data.get("followers_count", 0),
        following_count=data.get("followings_count", 0),
        track_count=data.get("track_count", 0),
        playlist_count=data.get("playlist_count", 0),
        repost_count=data.get("reposts_count", 0),
        likes_count=data.get("likes_count", 0) or data.get("public_favorites_count", 0),
        avatar_url=data.get("avatar_url", ""),
        profile_url=data.get("permalink_url", ""),
        join_date=_parse_datetime(data.get("created_at")),
        description=data.get("description") or "",
    )


def _normalize_track(raw: dict) -> TrackData:
    """Normalize a single SoundCloud track response."""
    tag_str = raw.get("tag_list", "")
    tags = [t.strip().strip('"') for t in tag_str.split(" ") if t.strip()] if tag_str else []

    return TrackData(
        platform_track_id=str(raw.get("id", "")),
        title=raw.get("title", ""),
        play_count=raw.get("playback_count", 0) or raw.get("plays_count", 0) or 0,
        like_count=raw.get("favoritings_count", 0) or raw.get("likes_count", 0) or 0,
        comment_count=raw.get("comment_count", 0) or 0,
        repost_count=raw.get("reposts_count", 0) or 0,
        download_count=raw.get("download_count", 0) or 0,
        duration_ms=raw.get("duration", 0) or 0,
        genre=raw.get("genre", "") or "",
        tag_list=tags,
        created_at=_parse_datetime(raw.get("created_at")),
        permalink_url=raw.get("permalink_url", ""),
        artwork_url=raw.get("artwork_url", "") or "",
        waveform_url=raw.get("waveform_url", "") or "",
        is_public=raw.get("sharing", "public") == "public",
    )


async def fetch_tracks(token: str, limit: int = 500) -> list[TrackData]:
    """Fetch full track catalog with pagination."""
    tracks: list[TrackData] = []
    page_size = 200  # SoundCloud max per page
    offset = 0

    while offset < limit:
        batch_size = min(page_size, limit - offset)
        data = await _sc_request(
            "/me/tracks",
            token,
            params={"limit": batch_size, "offset": offset},
        )

        if not data:
            break

        for raw in data:
            tracks.append(_normalize_track(raw))

        if len(data) < batch_size:
            break  # No more pages
        offset += batch_size

    logger.info("tracks_fetched", count=len(tracks))
    return tracks


async def exchange_code_for_token(
    code: str,
    client_id: str,
    client_secret: str,
    redirect_uri: str,
) -> dict:
    """Exchange OAuth authorization code for access token."""
    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.post(
            "https://api.soundcloud.com/oauth2/token",
            data={
                "grant_type": "authorization_code",
                "code": code,
                "client_id": client_id,
                "client_secret": client_secret,
                "redirect_uri": redirect_uri,
            },
        )

    if resp.status_code != 200:
        raise SoundCloudAPIError(
            f"Token exchange failed: {resp.status_code} — {resp.text}",
            status_code=resp.status_code,
        )

    return resp.json()
