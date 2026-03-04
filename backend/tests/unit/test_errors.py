"""Tests for error hierarchy."""

from src.shared.errors import (
    CybaOpError,
    QuotaExceededError,
    RateLimitError,
    SoundCloudAPIError,
    TierRestrictionError,
    TokenExpiredError,
)


def test_base_error():
    e = CybaOpError("test", "TEST_CODE")
    assert e.message == "test"
    assert e.error_code == "TEST_CODE"


def test_soundcloud_api_error():
    e = SoundCloudAPIError("API down", status_code=503)
    assert e.error_code == "SOUNDCLOUD_API_ERROR"
    assert e.status_code == 503


def test_token_expired():
    e = TokenExpiredError()
    assert e.error_code == "TOKEN_EXPIRED"


def test_quota_exceeded():
    e = QuotaExceededError(retry_after=120)
    assert e.retry_after == 120
    assert e.error_code == "QUOTA_EXCEEDED"


def test_rate_limit():
    e = RateLimitError(retry_after=30)
    assert e.retry_after == 30


def test_tier_restriction():
    e = TierRestrictionError()
    assert e.error_code == "TIER_RESTRICTION"
    assert "Pro" in e.message
