"""Workflow routes — stateful creator workflow endpoints (Pro tier only)."""

import json

from fastapi import APIRouter, Depends, Query

from src.api.auth import require_pro
from src.db.session import get_pool
from src.shared.logging import get_logger
from src.shared.models import (
    AdvanceRequest,
    CreateWorkflowRequest,
    HealthScoreHistoryResponse,
    HealthScorePoint,
    WorkflowListResponse,
    WorkflowSessionResponse,
)
from src.workflow.engine import WorkflowEngine
from src.workflow.steps.critique import (
    critique_track_step,
    fetch_tracks_step,
    portfolio_summary_step,
)
from src.workflow.steps.planner import (
    compile_plan_step,
    load_context_step,
    promotion_step,
    style_step,
    timing_step,
)
from src.workflow.steps.remediation import (
    load_incident_step,
    remediation_step_step,
    verify_outcome_step,
)

logger = get_logger("routes.workflows")
router = APIRouter(prefix="/workflows", tags=["workflows"])


def _get_engine() -> WorkflowEngine:
    """Create a WorkflowEngine with all step executors registered."""
    engine = WorkflowEngine()
    # Portfolio critique steps
    engine.register_executor("fetch_tracks", fetch_tracks_step)
    engine.register_executor("critique_track", critique_track_step)
    engine.register_executor("portfolio_summary", portfolio_summary_step)
    # Remediation steps
    engine.register_executor("load_incident", load_incident_step)
    engine.register_executor("remediation_step", remediation_step_step)
    engine.register_executor("verify_outcome", verify_outcome_step)
    # Release planner steps
    engine.register_executor("load_context", load_context_step)
    engine.register_executor("timing_recommendation", timing_step)
    engine.register_executor("style_recommendation", style_step)
    engine.register_executor("promotion_strategy", promotion_step)
    engine.register_executor("compile_plan", compile_plan_step)
    return engine


@router.post("", response_model=WorkflowSessionResponse)
async def create_workflow(body: CreateWorkflowRequest, user: dict = Depends(require_pro)):
    """Create a new workflow session."""
    user_id = user["sub"]
    engine = _get_engine()
    params = {**body.params, "user_id": user_id}
    return await engine.create_session(user_id, body.workflow_type, params)


@router.get("", response_model=WorkflowListResponse)
async def list_workflows(status: str | None = None, user: dict = Depends(require_pro)):
    """List workflow sessions for the current user."""
    user_id = user["sub"]
    engine = _get_engine()
    sessions = await engine.list_sessions(user_id, status)
    return WorkflowListResponse(sessions=sessions, total=len(sessions))


@router.get("/health-score/history", response_model=HealthScoreHistoryResponse)
async def health_score_history(user: dict = Depends(require_pro)):
    """Get health score history for the current user."""
    user_id = user["sub"]
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT score, components, explanation, computed_at "
            "FROM health_scores WHERE user_id = $1 "
            "ORDER BY computed_at DESC LIMIT 50",
            user_id,
        )
    history = [
        HealthScorePoint(
            score=r["score"],
            components=json.loads(r["components"]) if isinstance(r["components"], str) else dict(r["components"]),
            computed_at=r["computed_at"],
            explanation=r["explanation"],
        )
        for r in rows
    ]
    current = history[0].score if history else None
    return HealthScoreHistoryResponse(history=history, current_score=current)


@router.get("/{session_id}", response_model=WorkflowSessionResponse)
async def get_workflow(session_id: str, user: dict = Depends(require_pro)):
    """Get a specific workflow session."""
    user_id = user["sub"]
    engine = _get_engine()
    return await engine.get_session(session_id, user_id)


@router.post("/{session_id}/advance", response_model=WorkflowSessionResponse)
async def advance_workflow(session_id: str, body: AdvanceRequest, user: dict = Depends(require_pro)):
    """Advance the current step in a workflow session."""
    user_id = user["sub"]
    engine = _get_engine()
    return await engine.advance_session(session_id, user_id, body.user_input or None)


@router.post("/{session_id}/skip", response_model=WorkflowSessionResponse)
async def skip_step(session_id: str, user: dict = Depends(require_pro)):
    """Skip the current step if it's skippable."""
    user_id = user["sub"]
    engine = _get_engine()
    return await engine.skip_step(session_id, user_id)


@router.post("/{session_id}/pause", response_model=WorkflowSessionResponse)
async def pause_workflow(session_id: str, user: dict = Depends(require_pro)):
    """Pause an active workflow session."""
    user_id = user["sub"]
    engine = _get_engine()
    return await engine.pause_session(session_id, user_id)


@router.post("/{session_id}/resume", response_model=WorkflowSessionResponse)
async def resume_workflow(session_id: str, user: dict = Depends(require_pro)):
    """Resume a paused workflow session."""
    user_id = user["sub"]
    engine = _get_engine()
    return await engine.resume_session(session_id, user_id)
