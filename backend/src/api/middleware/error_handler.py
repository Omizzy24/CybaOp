"""Global error handling middleware — ported from agent platform."""

from fastapi import Request
from fastapi.responses import JSONResponse

from src.shared.errors import CybaOpError, QuotaExceededError, RateLimitError
from src.shared.logging import get_logger

logger = get_logger("error_handler")

STATUS_MAP = {
    "VALIDATION_ERROR": 422,
    "RATE_LIMIT_EXCEEDED": 429,
    "QUOTA_EXCEEDED": 429,
    "TOKEN_EXPIRED": 401,
    "TIER_RESTRICTION": 403,
    "SOUNDCLOUD_API_ERROR": 502,
    "DATABASE_ERROR": 503,
    "LLM_ERROR": 502,
    "INTERNAL_ERROR": 500,
}


async def cybaop_error_handler(request: Request, exc: CybaOpError) -> JSONResponse:
    """Handle CybaOp-specific errors."""
    status = STATUS_MAP.get(exc.error_code, 500)
    headers = {}

    if isinstance(exc, (RateLimitError, QuotaExceededError)):
        headers["Retry-After"] = str(exc.retry_after)

    logger.error("platform_error", error_code=exc.error_code, message=exc.message)

    body: dict = {
        "success": False,
        "message": exc.message,
        "error_code": exc.error_code,
    }

    if isinstance(exc, QuotaExceededError):
        body["cached_data_available"] = True
        body["retry_after_seconds"] = exc.retry_after

    return JSONResponse(status_code=status, content=body, headers=headers)
