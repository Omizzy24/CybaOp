"""Portfolio Critique step executors — fetch tracks, critique each, summarize."""

from src.db.queries import get_user_token
from src.shared.config import get_settings
from src.shared.errors import LLMError, WorkflowStateError
from src.shared.logging import get_logger
from src.tools.soundcloud import fetch_tracks

logger = get_logger("workflow.steps.critique")


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


async def fetch_tracks_step(context: dict, user_input: dict | None = None) -> dict:
    """Fetch the creator's tracks from SoundCloud and store metadata in context."""
    user_id = context.get("user_id")
    if not user_id:
        raise WorkflowStateError("Missing user_id in context")

    token = await get_user_token(user_id)
    if not token:
        raise WorkflowStateError(f"No SoundCloud token found for user {user_id}")

    logger.info("fetching_tracks", user_id=user_id)
    tracks = await fetch_tracks(token)

    track_ids = [t.platform_track_id for t in tracks]
    tracks_metadata = {}
    for t in tracks:
        tracks_metadata[t.platform_track_id] = {
            "title": t.title,
            "play_count": t.play_count,
            "like_count": t.like_count,
            "comment_count": t.comment_count,
            "repost_count": t.repost_count,
            "duration_ms": t.duration_ms,
            "genre": t.genre,
            "created_at": t.created_at.isoformat() if t.created_at else None,
            "permalink_url": t.permalink_url,
        }

    logger.info("tracks_fetched_for_critique", count=len(track_ids))
    return {
        "track_ids": track_ids,
        "tracks_metadata": tracks_metadata,
        "current_track_index": 0,
        "critiques": {},
        "skipped_tracks": [],
    }


async def critique_track_step(context: dict, user_input: dict | None = None) -> dict:
    """Send current track metadata + engagement metrics to Gemini for critique."""
    track_ids = context.get("track_ids", [])
    current_index = context.get("current_track_index", 0)
    tracks_metadata = context.get("tracks_metadata", {})
    critiques = dict(context.get("critiques", {}))

    if current_index >= len(track_ids):
        raise WorkflowStateError("No more tracks to critique")

    track_id = track_ids[current_index]
    meta = tracks_metadata.get(track_id, {})

    # Compute engagement rate for this track
    plays = meta.get("play_count", 0)
    engagement_rate = 0.0
    if plays > 0:
        engagement_rate = (
            meta.get("like_count", 0)
            + meta.get("comment_count", 0)
            + meta.get("repost_count", 0)
        ) / plays

    # Compute catalog average for relative comparison
    total_er = 0.0
    count = 0
    for tid, m in tracks_metadata.items():
        p = m.get("play_count", 0)
        if p > 0:
            total_er += (m.get("like_count", 0) + m.get("comment_count", 0) + m.get("repost_count", 0)) / p
            count += 1
    catalog_avg_er = total_er / count if count > 0 else 0.0

    prompt = (
        f"You are a music industry analyst. Analyze this SoundCloud track and provide honest, specific feedback.\n\n"
        f"Track: {meta.get('title', 'Unknown')}\n"
        f"Genre: {meta.get('genre', 'Unknown')}\n"
        f"Plays: {plays:,}\n"
        f"Likes: {meta.get('like_count', 0):,}\n"
        f"Comments: {meta.get('comment_count', 0):,}\n"
        f"Reposts: {meta.get('repost_count', 0):,}\n"
        f"Engagement Rate: {engagement_rate:.2%}\n"
        f"Catalog Average Engagement: {catalog_avg_er:.2%}\n"
        f"Duration: {meta.get('duration_ms', 0) // 1000}s\n\n"
        f"Respond with exactly four sections, each on its own line:\n"
        f"STRENGTH: (what's working well)\n"
        f"WEAKNESS: (what needs improvement)\n"
        f"DIAGNOSIS: (why the engagement numbers look the way they do)\n"
        f"RECOMMENDATION: (one specific, actionable improvement)\n"
    )

    raw = await _call_gemini(prompt)
    critique = _parse_critique(raw)

    critiques[track_id] = critique
    logger.info("track_critiqued", track_id=track_id, index=current_index)

    return {
        "critiques": critiques,
        "current_track_index": current_index + 1,
    }


def _parse_critique(raw: str) -> dict:
    """Parse Gemini response into structured critique fields."""
    result = {
        "strength": "",
        "weakness": "",
        "diagnosis": "",
        "recommendation": "",
    }

    lines = raw.strip().split("\n")
    current_key = None
    current_lines: list[str] = []

    key_map = {
        "STRENGTH": "strength",
        "WEAKNESS": "weakness",
        "DIAGNOSIS": "diagnosis",
        "RECOMMENDATION": "recommendation",
    }

    for line in lines:
        matched = False
        for prefix, key in key_map.items():
            if line.upper().startswith(prefix):
                if current_key:
                    result[current_key] = " ".join(current_lines).strip()
                current_key = key
                # Strip the prefix and colon
                remainder = line[len(prefix):].lstrip(":").strip()
                current_lines = [remainder] if remainder else []
                matched = True
                break
        if not matched and current_key:
            current_lines.append(line.strip())

    if current_key:
        result[current_key] = " ".join(current_lines).strip()

    # Fallback: if parsing failed, put the whole response in strength
    if not any(result.values()):
        result["strength"] = raw.strip()

    return result


async def portfolio_summary_step(context: dict, user_input: dict | None = None) -> dict:
    """Send all critiques to Gemini for cross-catalog pattern analysis."""
    critiques = context.get("critiques", {})
    tracks_metadata = context.get("tracks_metadata", {})

    if not critiques:
        return {"portfolio_summary": "No tracks were critiqued — nothing to summarize."}

    # Build summary prompt
    critique_text = ""
    for track_id, critique in critiques.items():
        meta = tracks_metadata.get(track_id, {})
        title = meta.get("title", track_id)
        critique_text += (
            f"\n--- {title} ---\n"
            f"Strength: {critique.get('strength', 'N/A')}\n"
            f"Weakness: {critique.get('weakness', 'N/A')}\n"
            f"Diagnosis: {critique.get('diagnosis', 'N/A')}\n"
            f"Recommendation: {critique.get('recommendation', 'N/A')}\n"
        )

    prompt = (
        f"You are a music industry analyst. Review these individual track critiques and identify "
        f"patterns across the entire catalog.\n\n"
        f"Individual critiques:{critique_text}\n\n"
        f"Provide a portfolio-level summary covering:\n"
        f"1. Common strengths across the catalog\n"
        f"2. Recurring weaknesses or patterns\n"
        f"3. Overall engagement diagnosis\n"
        f"4. Top 3 strategic recommendations for the artist\n"
    )

    summary = await _call_gemini(prompt)
    logger.info("portfolio_summary_generated", tracks_critiqued=len(critiques))

    return {"portfolio_summary": summary}
