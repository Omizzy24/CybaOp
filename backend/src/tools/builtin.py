"""Register CybaOp tools with the global registry."""

from pydantic import BaseModel, Field

from src.tools.registry import ToolDefinition, get_registry


class ProfileInput(BaseModel):
    token: str


class TracksInput(BaseModel):
    token: str
    limit: int = Field(default=500, ge=1, le=1000)


class EngagementInput(BaseModel):
    tracks: list[dict]


class TrendInput(BaseModel):
    tracks: list[dict]
    snapshots: list[dict] = []


def register_builtin_tools() -> None:
    """Register all CybaOp tools."""
    from src.tools.soundcloud import fetch_profile, fetch_tracks
    from src.tools.engagement import compute_metrics
    from src.tools.trends import analyze_trends

    registry = get_registry()

    registry.register(ToolDefinition(
        name="soundcloud_profile",
        description="Fetch and normalize SoundCloud artist profile",
        input_schema=ProfileInput,
        execute_fn=fetch_profile,
    ))
    registry.register(ToolDefinition(
        name="soundcloud_tracks",
        description="Fetch full track catalog with pagination",
        input_schema=TracksInput,
        execute_fn=fetch_tracks,
    ))
    registry.register(ToolDefinition(
        name="engagement_calculator",
        description="Compute engagement rates, performance scores, catalog health",
        input_schema=EngagementInput,
        execute_fn=compute_metrics,
    ))
    registry.register(ToolDefinition(
        name="trend_analyzer",
        description="Detect growth velocity, peak periods, release timing, strongest era",
        input_schema=TrendInput,
        execute_fn=analyze_trends,
    ))
