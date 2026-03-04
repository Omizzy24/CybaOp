"""Shared test fixtures."""

import os

import pytest

# Set test environment variables before any imports
os.environ.setdefault("SOUNDCLOUD_CLIENT_ID", "test-client-id")
os.environ.setdefault("SOUNDCLOUD_CLIENT_SECRET", "test-client-secret")
os.environ.setdefault("SOUNDCLOUD_REDIRECT_URI", "http://localhost:3000/callback")
os.environ.setdefault("GOOGLE_API_KEY", "test-google-key")
os.environ.setdefault("DATABASE_URL", "postgresql://test:test@localhost:5432/test")
os.environ.setdefault("JWT_SECRET", "test-secret-key")
os.environ.setdefault("ENV", "test")

from src.shared.models import TrackData, ProfileData
from datetime import datetime, timezone


@pytest.fixture
def sample_tracks() -> list[TrackData]:
    """Sample track data for testing."""
    return [
        TrackData(
            platform_track_id="1",
            title="Hit Track",
            play_count=10000,
            like_count=500,
            comment_count=100,
            repost_count=200,
            created_at=datetime(2025, 1, 15, 14, 0, tzinfo=timezone.utc),
        ),
        TrackData(
            platform_track_id="2",
            title="Moderate Track",
            play_count=3000,
            like_count=150,
            comment_count=30,
            repost_count=50,
            created_at=datetime(2025, 3, 10, 18, 0, tzinfo=timezone.utc),
        ),

        TrackData(
            platform_track_id="3",
            title="Sleeper Track",
            play_count=500,
            like_count=25,
            comment_count=5,
            repost_count=10,
            created_at=datetime(2025, 5, 20, 10, 0, tzinfo=timezone.utc),
        ),
        TrackData(
            platform_track_id="4",
            title="Viral Track",
            play_count=50000,
            like_count=5000,
            comment_count=1000,
            repost_count=2000,
            created_at=datetime(2025, 2, 6, 16, 0, tzinfo=timezone.utc),  # Thursday
        ),
        TrackData(
            platform_track_id="5",
            title="New Track",
            play_count=800,
            like_count=80,
            comment_count=20,
            repost_count=15,
            created_at=datetime(2025, 6, 1, 12, 0, tzinfo=timezone.utc),
        ),
    ]


@pytest.fixture
def sample_profile() -> ProfileData:
    """Sample profile data for testing."""
    return ProfileData(
        platform_user_id="12345",
        username="testartist",
        display_name="Test Artist",
        followers_count=5000,
        following_count=200,
        track_count=5,
        playlist_count=3,
        repost_count=50,
        likes_count=100,
        join_date=datetime(2023, 1, 1, tzinfo=timezone.utc),
    )
