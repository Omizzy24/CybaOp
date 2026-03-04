"""Custom exception hierarchy — ported from agent platform + SoundCloud domain."""


class CybaOpError(Exception):
    """Base exception for all CybaOp errors."""

    def __init__(self, message: str, error_code: str = "INTERNAL_ERROR"):
        self.message = message
        self.error_code = error_code
        super().__init__(message)


class ValidationError(CybaOpError):
    def __init__(self, message: str):
        super().__init__(message, "VALIDATION_ERROR")


class SoundCloudAPIError(CybaOpError):
    """SoundCloud API returned an error or is unavailable."""

    def __init__(self, message: str, status_code: int | None = None):
        self.status_code = status_code
        super().__init__(message, "SOUNDCLOUD_API_ERROR")


class TokenExpiredError(CybaOpError):
    """SoundCloud OAuth token has expired."""

    def __init__(self, message: str = "SoundCloud token expired — re-authentication required"):
        super().__init__(message, "TOKEN_EXPIRED")


class QuotaExceededError(CybaOpError):
    """SoundCloud API rate limit hit."""

    def __init__(self, message: str = "SoundCloud API rate limit exceeded", retry_after: int = 60):
        self.retry_after = retry_after
        super().__init__(message, "QUOTA_EXCEEDED")


class RateLimitError(CybaOpError):
    """CybaOp internal rate limit exceeded."""

    def __init__(self, message: str = "Rate limit exceeded", retry_after: int = 60):
        self.retry_after = retry_after
        super().__init__(message, "RATE_LIMIT_EXCEEDED")


class TierRestrictionError(CybaOpError):
    """User's tier doesn't allow this feature."""

    def __init__(self, message: str = "Upgrade to Pro for AI-powered insights"):
        super().__init__(message, "TIER_RESTRICTION")


class DatabaseError(CybaOpError):
    def __init__(self, message: str):
        super().__init__(message, "DATABASE_ERROR")


class LLMError(CybaOpError):
    def __init__(self, message: str):
        super().__init__(message, "LLM_ERROR")
