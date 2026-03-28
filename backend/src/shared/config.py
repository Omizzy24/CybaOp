"""Environment-based configuration using Pydantic BaseSettings."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """CybaOp configuration loaded from environment variables."""

    # SoundCloud OAuth
    soundcloud_client_id: str
    soundcloud_client_secret: str
    soundcloud_redirect_uri: str = ""

    # Google Gemini (for paid tier insights)
    google_api_key: str = ""

    # Database
    database_url: str = "postgresql://cybaop:cybaop@localhost:5432/cybaop"

    # JWT
    jwt_secret: str = "change-this-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expiry_hours: int = 720  # 30 days

    # API
    api_port: int = 8000
    port: int = 8000  # Railway/Render set PORT automatically
    api_host: str = "0.0.0.0"
    frontend_url: str = "http://localhost:3000"

    # Environment
    env: str = "development"
    log_level: str = "debug"
    rate_limit_per_minute: int = 30

    # Stripe (optional — app starts without them)
    stripe_secret_key: str = ""
    stripe_webhook_secret: str = ""
    stripe_pro_price_id: str = ""

    # Cache TTLs (seconds)
    cache_ttl_profile: int = 3600      # 1 hour
    cache_ttl_tracks: int = 1800       # 30 minutes
    cache_ttl_insights: int = 21600    # 6 hours

    # Guardrail thresholds
    data_freshness_warn_seconds: int = 21600   # 6 hours
    data_freshness_force_seconds: int = 86400  # 24 hours
    min_tracks_for_trends: int = 5
    confidence_threshold: float = 0.6

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    """Create and validate settings from environment."""
    return Settings()
