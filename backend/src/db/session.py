"""Database connection management with asyncpg — lean, no ORM."""

import ssl

import asyncpg

from src.shared.config import get_settings
from src.shared.logging import get_logger

logger = get_logger("db")

_pool: asyncpg.Pool | None = None


async def get_pool() -> asyncpg.Pool:
    """Get or create the connection pool."""
    global _pool
    if _pool is None:
        settings = get_settings()
        # Neon and most cloud Postgres providers require SSL
        ssl_context = None
        db_url = settings.database_url
        if "neon.tech" in db_url or "sslmode" in db_url:
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            # Strip query params that asyncpg doesn't understand
            if "?" in db_url:
                db_url = db_url.split("?")[0]

        _pool = await asyncpg.create_pool(
            db_url,
            min_size=1,
            max_size=5,  # conservative for serverless Postgres
            ssl=ssl_context,
        )
        logger.info("db_pool_created")
    return _pool


async def close_pool() -> None:
    """Close the connection pool on shutdown."""
    global _pool
    if _pool:
        await _pool.close()
        _pool = None
        logger.info("db_pool_closed")
