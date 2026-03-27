"""Pydantic domain models for CybaOp — all data contracts in one place."""

from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field


# --- Enums ---

class Tier(str, Enum):
    FREE = "free"
    PRO = "pro"
    ENTERPRISE = "enterprise"


# --- Normalized Domain Models (platform-agnostic) ---

class ProfileData(BaseModel):
    """Normalized artist profile — works for SoundCloud, Spotify, etc."""
    platform_user_id: str
    username: str
    display_name: str
    followers_count: int = 0
    following_count: int = 0
    track_count: int = 0
    playlist_count: int = 0
    repost_count: int = 0
    likes_count: int = 0
    avatar_url: str = ""
    profile_url: str = ""
    join_date: Optional[datetime] = None
    description: str = ""
    fetched_at: datetime = Field(default_factory=datetime.utcnow)


class TrackData(BaseModel):
    """Normalized track data."""
    platform_track_id: str
    title: str
    play_count: int = 0
    like_count: int = 0
    comment_count: int = 0
    repost_count: int = 0
    download_count: int = 0
    duration_ms: int = 0
    genre: str = ""
    tag_list: list[str] = []
    created_at: Optional[datetime] = None
    permalink_url: str = ""
    artwork_url: str = ""
    waveform_url: str = ""
    is_public: bool = True
    fetched_at: datetime = Field(default_factory=datetime.utcnow)


class TrackMetrics(BaseModel):
    """Computed metrics for a single track."""
    track_id: str
    title: str
    engagement_rate: float = 0.0  # (likes + comments + reposts) / plays
    comment_to_play_ratio: float = 0.0
    repost_to_like_ratio: float = 0.0
    performance_score: float = 0.0  # weighted composite
    plays_percentile: float = 0.0  # relative to catalog
    is_outlier: bool = False  # significantly over/underperforming
    outlier_direction: str = ""  # "over" or "under"


class AnalyticsMetrics(BaseModel):
    """Aggregated analytics across the catalog."""
    total_plays: int = 0
    total_likes: int = 0
    total_comments: int = 0
    total_reposts: int = 0
    avg_engagement_rate: float = 0.0
    catalog_concentration: float = 0.0  # % of plays from top 20% of tracks
    top_tracks: list[TrackMetrics] = []
    all_track_metrics: list[TrackMetrics] = []
    computed_at: datetime = Field(default_factory=datetime.utcnow)


class TrendPoint(BaseModel):
    """A single data point in a trend series."""
    date: datetime
    value: float
    label: str = ""


class PeakPeriod(BaseModel):
    """An identified peak performance period."""
    start_date: datetime
    end_date: datetime
    avg_engagement: float
    top_track: str
    description: str = ""


class TrendAnalysis(BaseModel):
    """Trend detection results."""
    growth_velocity_7d: float = 0.0
    growth_velocity_30d: float = 0.0
    growth_velocity_90d: float = 0.0
    growth_accelerating: bool = False
    peak_periods: list[PeakPeriod] = []
    best_release_day: Optional[str] = None  # e.g. "Thursday"
    best_release_hour: Optional[int] = None
    anomaly_tracks: list[str] = []  # track IDs significantly over/underperforming
    strongest_era_start: Optional[datetime] = None
    strongest_era_end: Optional[datetime] = None
    strongest_era_description: str = ""
    confidence: float = 0.0  # 0-1, based on data volume
    computed_at: datetime = Field(default_factory=datetime.utcnow)


class InsightItem(BaseModel):
    """A single AI-generated insight."""
    category: str  # "performance", "timing", "catalog", "growth"
    headline: str
    detail: str
    confidence: float = Field(ge=0.0, le=1.0)
    actionable: bool = False
    recommendation: str = ""


class AnalyticsReport(BaseModel):
    """The final assembled report returned to the frontend."""
    user_id: str
    profile: ProfileData
    track_count: int = 0
    top_tracks: list[TrackMetrics] = []
    metrics: Optional[AnalyticsMetrics] = None
    trends: Optional[TrendAnalysis] = None
    insights: list[InsightItem] = []
    eras: list[dict] = []
    era_fingerprint: Optional[dict] = None
    tier: Tier = Tier.FREE
    data_freshness_seconds: int = 0
    is_stale: bool = False
    correlation_id: str = ""
    processing_time_ms: int = 0
    nodes_executed: list[str] = []
    generated_at: datetime = Field(default_factory=datetime.utcnow)


# --- API Request/Response Models ---

class AnalyticsRequest(BaseModel):
    """Incoming analytics request from the frontend."""
    user_id: str = Field(..., min_length=1)
    force_refresh: bool = False

    model_config = ConfigDict(extra="ignore")


class AnalyticsResponse(BaseModel):
    """Structured API response wrapping the report."""
    request_id: str
    success: bool
    message: str
    report: Optional[AnalyticsReport] = None
    error_code: Optional[str] = None
    cached_data_available: bool = False
    cache_age_seconds: Optional[int] = None
    retry_after_seconds: Optional[int] = None
    processing_time_ms: int = 0


class AuthTokenRequest(BaseModel):
    """OAuth code exchange request."""
    code: str = Field(..., min_length=1)
    redirect_uri: str


class AuthTokenResponse(BaseModel):
    """JWT token returned after successful OAuth."""
    access_token: str
    token_type: str = "bearer"
    user_id: str
    username: str
    tier: Tier = Tier.FREE


class ErrorResponse(BaseModel):
    """Standardized error response."""
    request_id: str = ""
    success: bool = False
    message: str
    error_code: Optional[str] = None
    cached_data_available: bool = False
    cache_age_seconds: Optional[int] = None
    retry_after_seconds: Optional[int] = None


class HistoryDataPoint(BaseModel):
    """A single day's aggregate snapshot for the plays-over-time chart."""
    day: str  # ISO date string e.g. "2025-06-15"
    total_plays: int = 0
    total_likes: int = 0
    track_count: int = 0


class HistoryResponse(BaseModel):
    """Response for GET /analytics/history."""
    success: bool
    data: list[HistoryDataPoint] = []
    days_requested: int = 90
    message: str = ""
