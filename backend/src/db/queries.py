"""Database queries — thin layer over asyncpg."""

from datetime import datetime, timezone
from typing import Any
import uuid

from src.db.session import get_pool
from src.shared.logging import get_logger

logger = get_logger("db.queries")


async def upsert_user(
    soundcloud_user_id: str,
    username: str,
    display_name: str,
    soundcloud_token: str,
    avatar_url: str = "",
) -> str:
    """Create or update a user. Returns user_id."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        # Check if user exists
        row = await conn.fetchrow(
            "SELECT id FROM users WHERE soundcloud_user_id = $1",
            soundcloud_user_id,
        )
        if row:
            user_id = row["id"]
            await conn.execute(
                """UPDATE users
                   SET soundcloud_token = $1, username = $2,
                       display_name = $3, avatar_url = $4,
                       updated_at = NOW()
                   WHERE id = $5""",
                soundcloud_token, username, display_name,
                avatar_url, user_id,
            )
            logger.info("user_updated", user_id=user_id)
            return user_id

        user_id = str(uuid.uuid4())
        await conn.execute(
            """INSERT INTO users (id, soundcloud_user_id, username,
                   display_name, soundcloud_token, avatar_url)
               VALUES ($1, $2, $3, $4, $5, $6)""",
            user_id, soundcloud_user_id, username,
            display_name, soundcloud_token, avatar_url,
        )
        logger.info("user_created", user_id=user_id)
        return user_id


async def get_user(user_id: str) -> dict[str, Any] | None:
    """Fetch user by internal ID."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow("SELECT * FROM users WHERE id = $1", user_id)
        return dict(row) if row else None


async def get_user_token(user_id: str) -> str | None:
    """Get the SoundCloud token for a user."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT soundcloud_token FROM users WHERE id = $1", user_id
        )
        return row["soundcloud_token"] if row else None


async def update_last_analytics(user_id: str) -> None:
    """Mark when analytics were last run."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            "UPDATE users SET last_analytics_at = NOW() WHERE id = $1",
            user_id,
        )


async def save_track_snapshots(
    user_id: str, tracks: list[dict[str, Any]]
) -> int:
    """Batch insert track snapshots for trend tracking. Returns count."""
    if not tracks:
        return 0
    pool = await get_pool()
    async with pool.acquire() as conn:
        records = [
            (user_id, t["track_id"], t.get("title", ""),
             t.get("play_count", 0), t.get("like_count", 0),
             t.get("comment_count", 0), t.get("repost_count", 0))
            for t in tracks
        ]
        await conn.executemany(
            """INSERT INTO track_snapshots
               (user_id, track_id, title, play_count,
                like_count, comment_count, repost_count)
               SELECT $1, $2, $3, $4, $5, $6, $7
               WHERE NOT EXISTS (
                   SELECT 1 FROM track_snapshots
                   WHERE user_id = $1 AND track_id = $2
                   AND captured_at >= date_trunc('day', NOW())
               )""",
            records,
        )
        logger.info("snapshots_saved", user_id=user_id, count=len(records))
        return len(records)


async def get_track_history(
    user_id: str, track_id: str, limit: int = 90
) -> list[dict[str, Any]]:
    """Get historical snapshots for a track (for trend detection)."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """SELECT track_id, play_count, like_count, comment_count,
                      repost_count, captured_at
               FROM track_snapshots
               WHERE user_id = $1 AND track_id = $2
               ORDER BY captured_at DESC LIMIT $3""",
            user_id, track_id, limit,
        )
        return [dict(r) for r in rows]


async def get_all_track_history(
    user_id: str, limit_per_track: int = 30
) -> list[dict[str, Any]]:
    """Get recent snapshots for all tracks (for aggregate trends)."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """SELECT DISTINCT ON (track_id, date_trunc('day', captured_at))
                      track_id, title, play_count, like_count,
                      comment_count, repost_count, captured_at
               FROM track_snapshots
               WHERE user_id = $1
               ORDER BY track_id, date_trunc('day', captured_at) DESC,
                        captured_at DESC""",
            user_id,
        )
        return [dict(r) for r in rows]


async def get_plays_over_time(
    user_id: str, days: int = 90
) -> list[dict[str, Any]]:
    """Get daily aggregate play counts for the plays-over-time chart."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """SELECT date_trunc('day', captured_at)::date AS day,
                      SUM(play_count) AS total_plays,
                      SUM(like_count) AS total_likes,
                      COUNT(DISTINCT track_id) AS track_count
               FROM track_snapshots
               WHERE user_id = $1
                 AND captured_at >= NOW() - make_interval(days => $2)
               GROUP BY date_trunc('day', captured_at)::date
               ORDER BY day ASC""",
            user_id, days,
        )
        return [dict(r) for r in rows]


async def upgrade_user_tier(user_id: str, tier: str) -> None:
    """Update a user's subscription tier."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            "UPDATE users SET tier = $1, updated_at = NOW() WHERE id = $2",
            tier, user_id,
        )
    logger.info("tier_upgraded", user_id=user_id, tier=tier)


async def get_user_by_stripe_customer(customer_id: str) -> dict[str, Any] | None:
    """Find user by stripe_customer_id."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT * FROM users WHERE stripe_customer_id = $1", customer_id
        )
        return dict(row) if row else None


async def get_user_by_stripe_subscription(subscription_id: str) -> dict[str, Any] | None:
    """Find user by stripe_subscription_id."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT * FROM users WHERE stripe_subscription_id = $1", subscription_id
        )
        return dict(row) if row else None


async def update_user_stripe_info(
    user_id: str,
    stripe_customer_id: str | None = None,
    stripe_subscription_id: str | None = None,
    subscription_status: str | None = None,
    subscription_ends_at: datetime | None = None,
    tier: str | None = None,
) -> None:
    """Update Stripe-related fields on the user record. Only updates provided fields."""
    fields = []
    values = []
    idx = 1

    if stripe_customer_id is not None:
        fields.append(f"stripe_customer_id = ${idx}")
        values.append(stripe_customer_id)
        idx += 1
    if stripe_subscription_id is not None:
        fields.append(f"stripe_subscription_id = ${idx}")
        values.append(stripe_subscription_id)
        idx += 1
    if subscription_status is not None:
        fields.append(f"subscription_status = ${idx}")
        values.append(subscription_status)
        idx += 1
    if subscription_ends_at is not None:
        fields.append(f"subscription_ends_at = ${idx}")
        values.append(subscription_ends_at)
        idx += 1
    if tier is not None:
        fields.append(f"tier = ${idx}")
        values.append(tier)
        idx += 1

    if not fields:
        return

    fields.append("updated_at = NOW()")
    values.append(user_id)

    query = f"UPDATE users SET {', '.join(fields)} WHERE id = ${idx}"
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(query, *values)
    logger.info("user_stripe_info_updated", user_id=user_id)
