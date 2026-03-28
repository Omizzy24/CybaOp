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


SCHEMA_SQL_WORKFLOWS = """
CREATE TABLE IF NOT EXISTS workflow_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id TEXT NOT NULL REFERENCES users(id),
    workflow_type TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'active',
    current_step TEXT,
    context JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_wf_sessions_user_status
    ON workflow_sessions(user_id, status);

CREATE INDEX IF NOT EXISTS idx_wf_sessions_user_created
    ON workflow_sessions(user_id, created_at DESC);

CREATE TABLE IF NOT EXISTS workflow_steps (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES workflow_sessions(id) ON DELETE CASCADE,
    step_name TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    input JSONB NOT NULL DEFAULT '{}',
    output JSONB NOT NULL DEFAULT '{}',
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_wf_steps_session
    ON workflow_steps(session_id, step_name);

CREATE TABLE IF NOT EXISTS health_scores (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id TEXT NOT NULL REFERENCES users(id),
    score INTEGER NOT NULL CHECK (score >= 0 AND score <= 100),
    components JSONB NOT NULL DEFAULT '{}',
    explanation TEXT,
    computed_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_health_scores_user_time
    ON health_scores(user_id, computed_at DESC);

CREATE TABLE IF NOT EXISTS remediation_outcomes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES workflow_sessions(id) ON DELETE CASCADE,
    incident_type TEXT NOT NULL,
    original_severity TEXT NOT NULL,
    outcome TEXT NOT NULL DEFAULT 'unresolved',
    resolved_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_remediation_session
    ON remediation_outcomes(session_id);
"""


async def initialize_schema() -> None:
    """Create tables if they don't exist."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(SCHEMA_SQL)
        await conn.execute(SCHEMA_SQL_PART2)
        await conn.execute(SCHEMA_SQL_WORKFLOWS)
    logger.info("schema_initialized")
