"""FastAPI application factory for CybaOp backend."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.middleware.error_handler import cybaop_error_handler
from src.api.middleware.rate_limiter import RateLimiterMiddleware
from src.api.routes.analytics import router as analytics_router
from src.api.routes.auth import router as auth_router
from src.api.routes.health import router as health_router
from src.db.schema import initialize_schema
from src.db.session import close_pool
from src.shared.config import get_settings
from src.shared.errors import CybaOpError
from src.shared.logging import get_logger, setup_logging

logger = get_logger("app")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown lifecycle."""
    settings = get_settings()
    setup_logging(settings.log_level)
    logger.info("starting_cybaop", env=settings.env)

    # Initialize database schema
    try:
        await initialize_schema()
        logger.info("database_ready")
    except Exception as e:
        if settings.env == "development":
            logger.warning("database_init_skipped", error=str(e),
                          hint="Running without DB — auth will work, persistence won't")
        else:
            logger.error("database_init_failed", error=str(e))
            raise

    yield

    # Shutdown
    await close_pool()
    logger.info("cybaop_shutdown")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title="CybaOp API",
        version="0.1.0",
        description="The Intelligence Layer for SoundCloud Creators",
        lifespan=lifespan,
    )

    # CORS — allow the Next.js frontend
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.frontend_url, "http://localhost:3000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Rate limiter
    app.add_middleware(
        RateLimiterMiddleware,
        limit=settings.rate_limit_per_minute,
        window=60,
    )

    # Error handlers
    app.add_exception_handler(CybaOpError, cybaop_error_handler)

    # Routes
    app.include_router(health_router)
    app.include_router(auth_router)
    app.include_router(analytics_router)

    return app


app = create_app()
