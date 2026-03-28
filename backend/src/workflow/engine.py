"""Workflow Engine — session lifecycle, step execution, and state management."""

import json
import uuid
from datetime import datetime, timezone
from typing import Any, Callable, Coroutine

from src.db.session import get_pool
from src.shared.errors import (
    SoundCloudAPIError,
    WorkflowConcurrencyError,
    WorkflowNotFoundError,
    WorkflowStateError,
)
from src.shared.logging import get_logger
from src.shared.models import (
    StepStatus,
    WorkflowSessionResponse,
    WorkflowStepResponse,
    WorkflowStatus,
)
from src.workflow.registry import get_step_definition, get_workflow_steps

logger = get_logger("workflow.engine")

# Type alias for step executor functions
StepExecutor = Callable[[dict, dict | None], Coroutine[Any, Any, dict]]


class WorkflowEngine:
    """Core session lifecycle manager for stateful creator workflows."""

    def __init__(self) -> None:
        self._executors: dict[str, StepExecutor] = {}

    def register_executor(self, step_name: str, executor_fn: StepExecutor) -> None:
        """Register a step executor function by step name."""
        self._executors[step_name] = executor_fn

    # -------------------------------------------------------------------------
    # 3.1 — create_session, get_session, list_sessions
    # -------------------------------------------------------------------------

    async def create_session(
        self, user_id: str, workflow_type: str, params: dict | None = None
    ) -> WorkflowSessionResponse:
        """Create a new workflow session with all steps initialized."""
        steps = get_workflow_steps(workflow_type)  # raises ValueError if unknown
        session_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)
        context = params or {}
        first_step = steps[0].name

        pool = await get_pool()
        async with pool.acquire() as conn:
            async with conn.transaction():
                await conn.execute(
                    """
                    INSERT INTO workflow_sessions
                        (id, user_id, workflow_type, status, current_step, context, created_at, updated_at)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                    """,
                    uuid.UUID(session_id),
                    user_id,
                    workflow_type,
                    WorkflowStatus.ACTIVE.value,
                    first_step,
                    json.dumps(context),
                    now,
                    now,
                )
                for step_def in steps:
                    await conn.execute(
                        """
                        INSERT INTO workflow_steps
                            (id, session_id, step_name, status, input, output)
                        VALUES ($1, $2, $3, $4, $5, $6)
                        """,
                        uuid.uuid4(),
                        uuid.UUID(session_id),
                        step_def.name,
                        StepStatus.PENDING.value,
                        json.dumps({}),
                        json.dumps({}),
                    )

        logger.info(
            "session_created",
            session_id=session_id,
            workflow_type=workflow_type,
            user_id=user_id,
        )
        return await self.get_session(session_id, user_id)

    async def get_session(
        self, session_id: str, user_id: str
    ) -> WorkflowSessionResponse:
        """Load session from DB. Raises WorkflowNotFoundError if missing or wrong user."""
        pool = await get_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT id, user_id, workflow_type, status, current_step,
                       context, created_at, updated_at, completed_at
                FROM workflow_sessions
                WHERE id = $1
                """,
                uuid.UUID(session_id),
            )
            if row is None:
                raise WorkflowNotFoundError(session_id)
            if row["user_id"] != user_id:
                raise WorkflowNotFoundError(session_id)

            step_rows = await conn.fetch(
                """
                SELECT step_name, status, output, started_at, completed_at
                FROM workflow_steps
                WHERE session_id = $1
                ORDER BY id
                """,
                uuid.UUID(session_id),
            )

        return self._build_session_response(row, step_rows)

    async def list_sessions(
        self, user_id: str, status: str | None = None
    ) -> list[WorkflowSessionResponse]:
        """List sessions for a user, optionally filtered by status."""
        pool = await get_pool()
        async with pool.acquire() as conn:
            if status:
                session_rows = await conn.fetch(
                    """
                    SELECT id, user_id, workflow_type, status, current_step,
                           context, created_at, updated_at, completed_at
                    FROM workflow_sessions
                    WHERE user_id = $1 AND status = $2
                    ORDER BY created_at DESC
                    """,
                    user_id,
                    status,
                )
            else:
                session_rows = await conn.fetch(
                    """
                    SELECT id, user_id, workflow_type, status, current_step,
                           context, created_at, updated_at, completed_at
                    FROM workflow_sessions
                    WHERE user_id = $1
                    ORDER BY created_at DESC
                    """,
                    user_id,
                )

            results = []
            for srow in session_rows:
                step_rows = await conn.fetch(
                    """
                    SELECT step_name, status, output, started_at, completed_at
                    FROM workflow_steps
                    WHERE session_id = $1
                    ORDER BY id
                    """,
                    srow["id"],
                )
                results.append(self._build_session_response(srow, step_rows))

        return results

    # -------------------------------------------------------------------------
    # 3.2 — advance_session with optimistic locking and step execution
    # -------------------------------------------------------------------------

    async def advance_session(
        self, session_id: str, user_id: str, user_input: dict | None = None
    ) -> WorkflowSessionResponse:
        """Execute current step and advance. Uses optimistic locking."""
        pool = await get_pool()
        async with pool.acquire() as conn:
            # Load session
            row = await conn.fetchrow(
                """
                SELECT id, user_id, workflow_type, status, current_step,
                       context, created_at, updated_at, completed_at
                FROM workflow_sessions
                WHERE id = $1
                """,
                uuid.UUID(session_id),
            )
            if row is None:
                raise WorkflowNotFoundError(session_id)
            if row["user_id"] != user_id:
                raise WorkflowNotFoundError(session_id)

            if row["status"] != WorkflowStatus.ACTIVE.value:
                raise WorkflowStateError(
                    f"Cannot advance session in '{row['status']}' state"
                )

            workflow_type = row["workflow_type"]
            current_step = row["current_step"]
            context = json.loads(row["context"]) if isinstance(row["context"], str) else dict(row["context"])
            expected_updated_at = row["updated_at"]

            # Load step definition from registry
            step_def = get_step_definition(workflow_type, current_step)

            # Look up executor
            executor = self._executors.get(current_step)
            if executor is None:
                raise WorkflowStateError(
                    f"No executor registered for step '{current_step}'"
                )

            # Mark step as active
            now = datetime.now(timezone.utc)
            await conn.execute(
                """
                UPDATE workflow_steps
                SET status = $1, started_at = $2
                WHERE session_id = $3 AND step_name = $4
                """,
                StepStatus.ACTIVE.value,
                now,
                uuid.UUID(session_id),
                current_step,
            )

            # Execute the step
            try:
                step_output = await executor(context, user_input)
            except SoundCloudAPIError as exc:
                # Auto-pause on SoundCloud API errors
                logger.warning(
                    "soundcloud_api_error_auto_pause",
                    session_id=session_id,
                    step=current_step,
                    error=str(exc),
                )
                context["paused_reason"] = "soundcloud_unavailable"
                await conn.execute(
                    """
                    UPDATE workflow_sessions
                    SET status = $1, context = $2, updated_at = $3
                    WHERE id = $4 AND updated_at = $5
                    """,
                    WorkflowStatus.PAUSED.value,
                    json.dumps(context),
                    datetime.now(timezone.utc),
                    uuid.UUID(session_id),
                    expected_updated_at,
                )
                await conn.execute(
                    """
                    UPDATE workflow_steps
                    SET status = $1, output = $2, completed_at = $3
                    WHERE session_id = $4 AND step_name = $5
                    """,
                    StepStatus.FAILED.value,
                    json.dumps({"error": str(exc)}),
                    datetime.now(timezone.utc),
                    uuid.UUID(session_id),
                    current_step,
                )
                return await self.get_session(session_id, user_id)
            except Exception as exc:
                # Step failure: preserve prior context, mark step failed
                logger.error(
                    "step_execution_failed",
                    session_id=session_id,
                    step=current_step,
                    error=str(exc),
                )
                await conn.execute(
                    """
                    UPDATE workflow_steps
                    SET status = $1, output = $2, completed_at = $3
                    WHERE session_id = $4 AND step_name = $5
                    """,
                    StepStatus.FAILED.value,
                    json.dumps({"error": str(exc)}),
                    datetime.now(timezone.utc),
                    uuid.UUID(session_id),
                    current_step,
                )
                return await self.get_session(session_id, user_id)

            # Success path: persist step output, merge into context
            merged_context = {**context, **step_output}

            # Mark step completed
            step_completed_at = datetime.now(timezone.utc)
            await conn.execute(
                """
                UPDATE workflow_steps
                SET status = $1, output = $2, completed_at = $3
                WHERE session_id = $4 AND step_name = $5
                """,
                StepStatus.COMPLETED.value,
                json.dumps(step_output),
                step_completed_at,
                uuid.UUID(session_id),
                current_step,
            )

            # Determine next step
            if _should_repeat_step(workflow_type, current_step, merged_context):
                next_step = current_step
            else:
                next_step = self._get_next_step(workflow_type, current_step)

            # Update session with optimistic locking
            update_now = datetime.now(timezone.utc)
            if next_step is None:
                # Final step completed
                result = await conn.execute(
                    """
                    UPDATE workflow_sessions
                    SET status = $1, current_step = $2, context = $3,
                        updated_at = $4, completed_at = $5
                    WHERE id = $6 AND updated_at = $7
                    """,
                    WorkflowStatus.COMPLETED.value,
                    None,
                    json.dumps(merged_context),
                    update_now,
                    update_now,
                    uuid.UUID(session_id),
                    expected_updated_at,
                )
            else:
                result = await conn.execute(
                    """
                    UPDATE workflow_sessions
                    SET current_step = $1, context = $2, updated_at = $3
                    WHERE id = $4 AND updated_at = $5
                    """,
                    next_step,
                    json.dumps(merged_context),
                    update_now,
                    uuid.UUID(session_id),
                    expected_updated_at,
                )

            # Check optimistic lock
            rows_affected = int(result.split()[-1])
            if rows_affected == 0:
                raise WorkflowConcurrencyError(session_id)

            logger.info(
                "step_advanced",
                session_id=session_id,
                completed_step=current_step,
                next_step=next_step,
            )

        return await self.get_session(session_id, user_id)

    # -------------------------------------------------------------------------
    # 3.3 — skip_step, pause_session, resume_session
    # -------------------------------------------------------------------------

    async def skip_step(
        self, session_id: str, user_id: str
    ) -> WorkflowSessionResponse:
        """Skip current step if it's skippable. Advances to next step."""
        pool = await get_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT id, user_id, workflow_type, status, current_step,
                       context, created_at, updated_at, completed_at
                FROM workflow_sessions
                WHERE id = $1
                """,
                uuid.UUID(session_id),
            )
            if row is None:
                raise WorkflowNotFoundError(session_id)
            if row["user_id"] != user_id:
                raise WorkflowNotFoundError(session_id)

            if row["status"] != WorkflowStatus.ACTIVE.value:
                raise WorkflowStateError(
                    f"Cannot skip step in '{row['status']}' state"
                )

            workflow_type = row["workflow_type"]
            current_step = row["current_step"]
            context = json.loads(row["context"]) if isinstance(row["context"], str) else dict(row["context"])
            expected_updated_at = row["updated_at"]

            # Validate step is skippable
            step_def = get_step_definition(workflow_type, current_step)
            if not step_def.skippable:
                raise WorkflowStateError(
                    f"Step '{current_step}' is not skippable"
                )

            # Mark step as skipped
            now = datetime.now(timezone.utc)
            await conn.execute(
                """
                UPDATE workflow_steps
                SET status = $1, completed_at = $2
                WHERE session_id = $3 AND step_name = $4
                """,
                StepStatus.SKIPPED.value,
                now,
                uuid.UUID(session_id),
                current_step,
            )

            # Advance to next step
            next_step = self._get_next_step(workflow_type, current_step)
            update_now = datetime.now(timezone.utc)

            if next_step is None:
                result = await conn.execute(
                    """
                    UPDATE workflow_sessions
                    SET status = $1, current_step = $2, context = $3,
                        updated_at = $4, completed_at = $5
                    WHERE id = $6 AND updated_at = $7
                    """,
                    WorkflowStatus.COMPLETED.value,
                    None,
                    json.dumps(context),
                    update_now,
                    update_now,
                    uuid.UUID(session_id),
                    expected_updated_at,
                )
            else:
                result = await conn.execute(
                    """
                    UPDATE workflow_sessions
                    SET current_step = $1, context = $2, updated_at = $3
                    WHERE id = $4 AND updated_at = $5
                    """,
                    next_step,
                    json.dumps(context),
                    update_now,
                    uuid.UUID(session_id),
                    expected_updated_at,
                )

            rows_affected = int(result.split()[-1])
            if rows_affected == 0:
                raise WorkflowConcurrencyError(session_id)

            logger.info(
                "step_skipped",
                session_id=session_id,
                skipped_step=current_step,
                next_step=next_step,
            )

        return await self.get_session(session_id, user_id)

    async def pause_session(
        self, session_id: str, user_id: str
    ) -> WorkflowSessionResponse:
        """Pause an active session."""
        pool = await get_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT id, user_id, status, updated_at
                FROM workflow_sessions
                WHERE id = $1
                """,
                uuid.UUID(session_id),
            )
            if row is None:
                raise WorkflowNotFoundError(session_id)
            if row["user_id"] != user_id:
                raise WorkflowNotFoundError(session_id)

            if row["status"] != WorkflowStatus.ACTIVE.value:
                raise WorkflowStateError(
                    f"Cannot pause session in '{row['status']}' state — only active sessions can be paused"
                )

            now = datetime.now(timezone.utc)
            result = await conn.execute(
                """
                UPDATE workflow_sessions
                SET status = $1, updated_at = $2
                WHERE id = $3 AND updated_at = $4
                """,
                WorkflowStatus.PAUSED.value,
                now,
                uuid.UUID(session_id),
                row["updated_at"],
            )
            rows_affected = int(result.split()[-1])
            if rows_affected == 0:
                raise WorkflowConcurrencyError(session_id)

            logger.info("session_paused", session_id=session_id)

        return await self.get_session(session_id, user_id)

    async def resume_session(
        self, session_id: str, user_id: str
    ) -> WorkflowSessionResponse:
        """Resume a paused session."""
        pool = await get_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT id, user_id, status, updated_at
                FROM workflow_sessions
                WHERE id = $1
                """,
                uuid.UUID(session_id),
            )
            if row is None:
                raise WorkflowNotFoundError(session_id)
            if row["user_id"] != user_id:
                raise WorkflowNotFoundError(session_id)

            if row["status"] != WorkflowStatus.PAUSED.value:
                raise WorkflowStateError(
                    f"Cannot resume session in '{row['status']}' state — only paused sessions can be resumed"
                )

            now = datetime.now(timezone.utc)
            result = await conn.execute(
                """
                UPDATE workflow_sessions
                SET status = $1, updated_at = $2
                WHERE id = $3 AND updated_at = $4
                """,
                WorkflowStatus.ACTIVE.value,
                now,
                uuid.UUID(session_id),
                row["updated_at"],
            )
            rows_affected = int(result.split()[-1])
            if rows_affected == 0:
                raise WorkflowConcurrencyError(session_id)

            logger.info("session_resumed", session_id=session_id)

        return await self.get_session(session_id, user_id)

    # -------------------------------------------------------------------------
    # Helpers
    # -------------------------------------------------------------------------

    def _get_next_step(
        self, workflow_type: str, current_step: str
    ) -> str | None:
        """Return the next step name, or None if current is the last step."""
        steps = get_workflow_steps(workflow_type)
        for i, step_def in enumerate(steps):
            if step_def.name == current_step:
                if i + 1 < len(steps):
                    return steps[i + 1].name
                return None
        return None

    def _build_session_response(
        self, session_row: Any, step_rows: list[Any]
    ) -> WorkflowSessionResponse:
        """Convert DB rows into a WorkflowSessionResponse model."""
        workflow_type = session_row["workflow_type"]
        registry_steps = get_workflow_steps(workflow_type)
        step_defs_by_name = {s.name: s for s in registry_steps}

        steps = []
        for srow in step_rows:
            step_name = srow["step_name"]
            step_def = step_defs_by_name.get(step_name)
            output_raw = srow["output"]
            if isinstance(output_raw, str):
                output = json.loads(output_raw)
            elif output_raw is None:
                output = None
            else:
                output = dict(output_raw)

            steps.append(
                WorkflowStepResponse(
                    step_name=step_name,
                    label=step_def.label if step_def else step_name,
                    status=StepStatus(srow["status"]),
                    output=output if output else None,
                    skippable=step_def.skippable if step_def else False,
                    started_at=srow["started_at"],
                    completed_at=srow["completed_at"],
                )
            )

        context_raw = session_row["context"]
        if isinstance(context_raw, str):
            context = json.loads(context_raw)
        else:
            context = dict(context_raw) if context_raw else {}

        return WorkflowSessionResponse(
            id=str(session_row["id"]),
            workflow_type=session_row["workflow_type"],
            status=WorkflowStatus(session_row["status"]),
            current_step=session_row["current_step"],
            steps=steps,
            context=context,
            created_at=session_row["created_at"],
            updated_at=session_row["updated_at"],
            completed_at=session_row["completed_at"],
        )


# -------------------------------------------------------------------------
# 3.4 — _should_repeat_step (module-level for testability)
# -------------------------------------------------------------------------

def _should_repeat_step(
    workflow_type: str, step_name: str, context: dict
) -> bool:
    """Check if a repeating step should execute again based on context indices."""
    if workflow_type == "portfolio_critique" and step_name == "critique_track":
        current_index = context.get("current_track_index", 0)
        track_ids = context.get("track_ids", [])
        return current_index < len(track_ids)

    if workflow_type == "remediation" and step_name == "remediation_step":
        current_index = context.get("current_step_index", 0)
        remediation_steps = context.get("remediation_steps", [])
        return current_index < len(remediation_steps)

    return False
