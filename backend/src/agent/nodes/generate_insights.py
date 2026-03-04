"""Generate insights node — LLM synthesizes metrics and trends into actionable insights."""

import json

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI

from src.agent.state import AnalyticsState
from src.shared.config import get_settings
from src.shared.logging import get_logger
from src.shared.models import InsightItem

logger = get_logger("node.generate_insights")

SYSTEM_PROMPT = """You are CybaOp, an AI music analytics assistant for SoundCloud creators.
You analyze metrics and trends to provide actionable insights.
Be specific with numbers. Be honest about confidence levels.
Speak like a knowledgeable music industry advisor, not a robot.
Return your response as a JSON array of insight objects."""

INSIGHT_PROMPT = """Analyze this SoundCloud artist's data and generate 3-5 actionable insights.

Profile: {profile_summary}

Catalog Metrics:
- Total plays: {total_plays:,}
- Total likes: {total_likes:,}
- Average engagement rate: {avg_engagement:.2%}
- Catalog concentration: {concentration:.0%} of plays from top 20% of tracks

Top Tracks:
{top_tracks}

Trends:
- 7-day growth velocity: {gv_7d:.2%}
- 30-day growth velocity: {gv_30d:.2%}
- Growth accelerating: {accelerating}
- Best release day: {best_day}
- Strongest era: {strongest_era}

Return a JSON array where each object has:
- "category": one of "performance", "timing", "catalog", "growth"
- "headline": short punchy insight (1 sentence)
- "detail": explanation with specific numbers (2-3 sentences)
- "confidence": 0.0-1.0 based on data quality
- "actionable": true/false
- "recommendation": specific action to take (if actionable)

Return ONLY the JSON array, no markdown."""


async def generate_insights_node(state: AnalyticsState) -> dict:
    """Generate AI insights from metrics and trends."""
    try:
        settings = get_settings()
        if not settings.google_api_key:
            logger.warning("no_google_api_key_skipping_insights")
            return {
                "insights": [],
                "nodes_executed": state.get("nodes_executed", []) + ["generate_insights"],
            }

        profile = state.get("profile_data")
        metrics = state.get("metrics")
        trends = state.get("trends")

        if not profile or not metrics:
            return {
                "insights": [],
                "nodes_executed": state.get("nodes_executed", []) + ["generate_insights"],
            }

        # Build top tracks summary
        top_tracks_str = "\n".join(
            f"  - '{t.title}': score={t.performance_score:.3f}, "
            f"engagement={t.engagement_rate:.2%}, outlier={t.is_outlier}"
            for t in (metrics.top_tracks or [])[:5]
        )

        prompt = INSIGHT_PROMPT.format(
            profile_summary=f"{profile.display_name} (@{profile.username}), "
                           f"{profile.followers_count:,} followers, "
                           f"{profile.track_count} tracks",
            total_plays=metrics.total_plays,
            total_likes=metrics.total_likes,
            avg_engagement=metrics.avg_engagement_rate,
            concentration=metrics.catalog_concentration,
            top_tracks=top_tracks_str or "No tracks available",
            gv_7d=trends.growth_velocity_7d if trends else 0,
            gv_30d=trends.growth_velocity_30d if trends else 0,
            accelerating=trends.growth_accelerating if trends else False,
            best_day=trends.best_release_day if trends else "Unknown",
            strongest_era=trends.strongest_era_description if trends else "Not enough data",
        )

        llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash",
            google_api_key=settings.google_api_key,
            temperature=0.4,
            max_output_tokens=2048,
        )

        response = await llm.ainvoke([
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=prompt),
        ])

        # Parse JSON response
        raw = response.content.strip()
        # Strip markdown code fences if present
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[1] if "\n" in raw else raw[3:]
            if raw.endswith("```"):
                raw = raw[:-3]
            raw = raw.strip()

        insights_data = json.loads(raw)
        insights = [InsightItem(**item) for item in insights_data]

        # Apply confidence threshold
        threshold = settings.confidence_threshold
        for insight in insights:
            if insight.confidence < threshold:
                insight.headline = f"[Low confidence] {insight.headline}"

        logger.info("insights_generated", count=len(insights))

        return {
            "insights": insights,
            "nodes_executed": state.get("nodes_executed", []) + ["generate_insights"],
        }
    except json.JSONDecodeError as e:
        logger.error("insight_parse_failed", error=str(e))
        return {
            "insights": [],
            "nodes_executed": state.get("nodes_executed", []) + ["generate_insights"],
            "error": f"Failed to parse LLM insights: {e}",
        }
    except Exception as e:
        logger.error("generate_insights_failed", error=str(e))
        return {
            "insights": [],
            "nodes_executed": state.get("nodes_executed", []) + ["generate_insights"],
            "error": str(e),
        }
