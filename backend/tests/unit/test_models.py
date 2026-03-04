"""Tests for Pydantic model validation."""

import pytest
from pydantic import ValidationError

from src.shared.models import (
    AnalyticsRequest,
    AuthTokenRequest,
    InsightItem,
    ProfileData,
    Tier,
    TrackData,
    TrackMetrics,
)


def test_profile_data_defaults():
    p = ProfileData(platform_user_id="1", username="test", display_name="Test")
    assert p.followers_count == 0
    assert p.fetched_at is not None


def test_track_data_defaults():
    t = TrackData(platform_track_id="1", title="Test")
    assert t.play_count == 0
    assert t.is_public is True


def test_analytics_request_validation():
    req = AnalyticsRequest(user_id="user-1")
    assert req.force_refresh is False


def test_analytics_request_empty_user_id():
    with pytest.raises(ValidationError):
        AnalyticsRequest(user_id="")


def test_insight_item_confidence_bounds():
    item = InsightItem(
        category="performance", headline="Test", detail="Detail", confidence=0.8
    )
    assert item.confidence == 0.8

    with pytest.raises(ValidationError):
        InsightItem(
            category="performance", headline="Test", detail="Detail", confidence=1.5
        )


def test_tier_enum():
    assert Tier.FREE.value == "free"
    assert Tier.PRO.value == "pro"
    assert Tier("enterprise") == Tier.ENTERPRISE


def test_track_metrics_defaults():
    m = TrackMetrics(track_id="1", title="Test")
    assert m.engagement_rate == 0.0
    assert m.is_outlier is False
