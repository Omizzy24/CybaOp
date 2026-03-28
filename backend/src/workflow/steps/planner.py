"""Release Planner step executors — load context, timing, style, promotion, compile."""

from datetime import datetime, timezone

from src.shared.config import get_settings
from src.shared.errors import LLMError, WorkflowStateError
from src.shared.logging import get_logger

logger = get_logger("workflow.steps.planner")


async def _call_gemini(prompt: str) -> str:
    """Call Gemini LLM via LangChain. Raises LLMError on failure."""
    try:
        from langchain_google_genai import ChatGoogleGenerativeAI

        settings = get_settings()
        llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash",
            google_api_key=settings.google_api_key,
        )
        response = await llm.ainvoke(prompt)
        return response.content
    except Exception as exc:
        raise LLMError(f"Gemini call failed: {exc}") from exc


async def load_context_step(context: dict, user_input: dict | None = None) -> dict:
    """Load trends, era fingerprint, and catalog metrics from existing analytics tools."""
    from src.db.queries import get_user_token
    from src.tools.engagement import compute_metrics
    from src.tools.soundcloud import fetch_tracks
    from src.tools.trends import analyze_trends, fingerprint_era

    user_id = context.get("user_id")
    if not user_id:
        raise WorkflowStateError("Missing user_id in context")

    token = await get_user_token(user_id)
    if not token:
        raise WorkflowStateError(f"No SoundCloud token found for user {user_id}")

    tracks = await fetch_tracks(token)
    trends = analyze_trends(tracks)
    era_fp = fingerprint_era(tracks)
    metrics = compute_metrics(tracks)

    logger.info(
        "planner_context_loaded",
        user_id=user_id,
        track_count=len(tracks),
        best_day=trends.best_release_day,
        best_hour=trends.best_release_hour,
    )

    return {
        "best_release_day": trends.best_release_day,
        "best_release_hour": trends.best_release_hour,
        "era_fingerprint": era_fp,
        "catalog_concentration": metrics.catalog_concentration,
        "growth_velocity_7d": trends.growth_velocity_7d,
    }


async def timing_step(context: dict, user_input: dict | None = None) -> dict:
    """Send timing data to Gemini, accept user override."""
    best_day = context.get("best_release_day", "Unknown")
    best_hour = context.get("best_release_hour")
    growth_velocity = context.get("growth_velocity_7d", 0.0)

    prompt = (
        f"You are a music release strategist. Based on this creator's historical data, "
        f"recommend the optimal release timing.\n\n"
        f"Best performing release day: {best_day}\n"
        f"Best performing release hour: {best_hour}\n"
        f"7-day growth velocity: {growth_velocity:.2%}\n\n"
        f"Provide a brief recommendation with:\n"
        f"1. Recommended day of the week\n"
        f"2. Recommended hour (24h format)\n"
        f"3. A one-paragraph rationale\n"
    )

    raw = await _call_gemini(prompt)

    timing_override = None
    if user_input and "override" in user_input:
        timing_override = user_input["override"]

    return {
        "timing_recommendation": {
            "day": best_day or "Thursday",
            "hour": best_hour if best_hour is not None else 14,
            "rationale": raw,
        },
        "timing_override": timing_override,
    }


async def style_step(context: dict, user_input: dict | None = None) -> dict:
    """Send genre/style data to Gemini, accept user override."""
    era_fp = context.get("era_fingerprint", {})
    concentration = context.get("catalog_concentration", 0.0)
    dominant_genre = era_fp.get("dominant_genre", "Unknown")
    genre_dist = era_fp.get("genre_distribution", {})

    prompt = (
        f"You are a music style advisor. Based on this creator's catalog profile, "
        f"recommend what genre/style their next release should target.\n\n"
        f"Dominant genre: {dominant_genre}\n"
        f"Genre distribution: {genre_dist}\n"
        f"Catalog concentration: {concentration:.2%}\n"
        f"Average engagement: {era_fp.get('avg_engagement', 0):.4f}\n\n"
        f"Provide a recommendation with:\n"
        f"1. Recommended genre/style direction\n"
        f"2. A one-paragraph rationale explaining why\n"
    )

    raw = await _call_gemini(prompt)

    style_override = None
    if user_input and "override" in user_input:
        style_override = user_input["override"]

    return {
        "style_recommendation": {
            "genre": dominant_genre,
            "rationale": raw,
        },
        "style_override": style_override,
    }


async def promotion_step(context: dict, user_input: dict | None = None) -> dict:
    """Send growth data to Gemini, accept user override."""
    growth_velocity = context.get("growth_velocity_7d", 0.0)
    concentration = context.get("catalog_concentration", 0.0)
    era_fp = context.get("era_fingerprint", {})

    prompt = (
        f"You are a music promotion strategist. Based on this creator's growth data, "
        f"build a promotion plan for their next release.\n\n"
        f"7-day growth velocity: {growth_velocity:.2%}\n"
        f"Catalog concentration: {concentration:.2%}\n"
        f"Average plays per track: {era_fp.get('avg_plays', 0)}\n"
        f"Track count: {era_fp.get('track_count', 0)}\n\n"
        f"Provide 3-5 specific promotional actions with expected impact for each.\n"
    )

    raw = await _call_gemini(prompt)

    promotion_override = None
    if user_input and "override" in user_input:
        promotion_override = user_input["override"]

    return {
        "promotion_strategy": {
            "actions": [raw],
            "rationale": raw,
        },
        "promotion_override": promotion_override,
    }


async def compile_plan_step(context: dict, user_input: dict | None = None) -> dict:
    """Assemble all recommendations (with overrides) into final release plan."""
    timing = context.get("timing_recommendation", {})
    timing_override = context.get("timing_override")
    style = context.get("style_recommendation", {})
    style_override = context.get("style_override")
    promotion = context.get("promotion_strategy", {})
    promotion_override = context.get("promotion_override")

    # Apply overrides
    if timing_override:
        timing = {**timing, **timing_override} if isinstance(timing_override, dict) else timing
    if style_override:
        style = {**style, **style_override} if isinstance(style_override, dict) else style
    if promotion_override:
        promotion = {**promotion, **promotion_override} if isinstance(promotion_override, dict) else promotion

    release_plan = {
        "timing": timing,
        "style": style,
        "promotion": promotion,
        "compiled_at": datetime.now(timezone.utc).isoformat(),
    }

    logger.info("release_plan_compiled")

    return {"release_plan": release_plan}
