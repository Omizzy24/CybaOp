"""Database schema initialization — raw SQL, no ORM overhead."""

from src.db.session import get_pool
from src.shared.logging import get_logger

logger = get_logger("db.schema")

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    soundcloud_user_id TEXT UNIQUE NOT NULL,
    username TEXT NOT NULL,
    display_name TEXT NOT NULL DEFAULT '',
    soundcloud_token TEXT NOT NULL,
    tier TEXT NOT NULL DEFAULT 'free',
    avatar_url TEXT NOT NULL DEFAULT '',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_analytics_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_users_sc_id
    ON users(soundcloud_user_id);

CREATE TABLE IF NOT EXISTS track_snapshots (
    id BIGSERIAL PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES users(id),
    track_id TEXT NOT NULL,
    title TEXT NOT NULL DEFAULT '',
    play_count INT NOT NULL DEFAULT 0,
    like_count INT NOT NULL DEFAULT 0,
    comment_count INT NOT NULL DEFAULT 0,
    repost_count INT NOT NULL DEFAULT 0,
    captured_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
"""

SCHEMA_SQL_PART2 = """
CREATE INDEX IF NOT EXISTS idx_snapshots_user_track
    ON track_snapshots(user_id, track_id, captured_at DESC);

CREATE INDEX IF NOT EXISTS idx_snapshots_user_time
    ON track_snapshots(user_id, captured_at DESC);
"""


async def initialize_schema() -> None:
    """Create tables if they don't exist."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(SCHEMA_SQL)
        await conn.execute(SCHEMA_SQL_PART2)
    logger.info("schema_initialized")
