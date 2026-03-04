"""Sliding window rate limiter — ported from agent platform."""

import asyncio
import time

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from src.shared.config import get_settings


class RateLimiterMiddleware(BaseHTTPMiddleware):
    """Per-user sliding window rate limiter."""

    def __init__(self, app, limit: int = 30, window: int = 60):
        super().__init__(app)
        self.limit = limit
        self.window = window
        self._requests: dict[str, list[float]] = {}
        self._lock = asyncio.Lock()

    def _get_key(self, request: Request) -> str:
        user_id = request.headers.get("X-User-ID")
        if user_id:
            return f"user:{user_id}"
        return f"ip:{request.client.host}" if request.client else "ip:unknown"

    async def dispatch(self, request: Request, call_next) -> Response:
        if request.url.path == "/health":
            return await call_next(request)

        key = self._get_key(request)
        now = time.time()

        async with self._lock:
            if key not in self._requests:
                self._requests[key] = []
            self._requests[key] = [
                ts for ts in self._requests[key] if now - ts < self.window
            ]
            if len(self._requests[key]) >= self.limit:
                oldest = self._requests[key][0]
                retry_after = int(self.window - (now - oldest)) + 1
                return JSONResponse(
                    status_code=429,
                    content={
                        "success": False,
                        "message": "Rate limit exceeded",
                        "error_code": "RATE_LIMIT_EXCEEDED",
                        "retry_after_seconds": retry_after,
                    },
                    headers={"Retry-After": str(retry_after)},
                )
            self._requests[key].append(now)

        return await call_next(request)
