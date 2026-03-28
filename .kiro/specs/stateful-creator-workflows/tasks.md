# Implementation Plan: Stateful Creator Workflows

## Overview

Incremental implementation of the workflow engine, three workflow types, health score, API routes, and frontend UI. Each task builds on the previous, starting with shared models and DB schema, then the engine core, then workflow-specific logic, then API wiring, and finally frontend integration. Property-based tests validate correctness properties from the design; unit tests cover edge cases.

## Tasks

- [x] 1. Add shared models, error types, and database schema
  - [x] 1.1 Add workflow error types to `backend/src/shared/errors.py`
    - Add `WorkflowError`, `WorkflowNotFoundError`, `WorkflowConcurrencyError`, `WorkflowStateError` as defined in the design
    - _Requirements: 1.5, 1.7_

  - [x] 1.2 Add workflow Pydantic models to `backend/src/shared/models.py`
    - Add enums: `WorkflowStatus`, `StepStatus`, `RemediationOutcome`
    - Add request models: `CreateWorkflowRequest`, `AdvanceRequest`
    - Add response models: `WorkflowStepResponse`, `WorkflowSessionResponse`, `WorkflowListResponse`, `HealthScorePoint`, `HealthScoreHistoryResponse`
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5_

  - [x] 1.3 Add workflow tables to `backend/src/db/schema.py`
    - Add `workflow_sessions`, `workflow_steps`, `health_scores`, `remediation_outcomes` tables with indexes as defined in the design
    - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5_

  - [ ]* 1.4 Write unit tests for new error types and models
    - Test `WorkflowError` hierarchy inherits from `CybaOpError`
    - Test `WorkflowStatus`, `StepStatus`, `RemediationOutcome` enum values
    - Test `CreateWorkflowRequest` and `AdvanceRequest` validation
    - Test `WorkflowSessionResponse` serialization
    - Add to `backend/tests/unit/test_errors.py` and `backend/tests/unit/test_models.py`
    - _Requirements: 1.1, 6.1_

- [x] 2. Implement Workflow Registry
  - [x] 2.1 Create `backend/src/workflow/__init__.py` and `backend/src/workflow/registry.py`
    - Define `StepDefinition` dataclass with `name`, `label`, `requires_input`, `skippable`
    - Define `WORKFLOW_TYPES` dict with step sequences for `portfolio_critique`, `remediation`, `release_planner`
    - Implement `get_workflow_steps()` and `get_step_definition()` functions
    - _Requirements: 1.6, 2.1, 3.1, 4.1_

  - [ ]* 2.2 Write unit tests for Workflow Registry
    - Test `get_workflow_steps` returns correct step lists for each workflow type
    - Test `get_step_definition` finds steps by name
    - Test `get_workflow_steps` raises `ValueError` for unknown workflow type
    - Test `get_step_definition` raises `ValueError` for unknown step name
    - Add to `backend/tests/unit/test_workflow_registry.py`
    - _Requirements: 1.6_

- [x] 3. Implement Workflow Engine core
  - [x] 3.1 Create `backend/src/workflow/engine.py` with `WorkflowEngine` class
    - Implement `create_session()`: generate UUID, insert `workflow_sessions` row with status `active`, create `workflow_steps` rows for all steps in the registry, set `current_step` to first step
    - Implement `get_session()`: load session from DB, raise `WorkflowNotFoundError` if missing, verify `user_id` ownership
    - Implement `list_sessions()`: query sessions by `user_id`, optional status filter
    - Use existing asyncpg pool from `src/db/session.py`
    - _Requirements: 1.1, 1.2, 6.1, 6.2, 6.4_

  - [x] 3.2 Implement `advance_session()` with optimistic locking and step execution
    - Validate session is `active`, load current step definition from registry
    - Use `UPDATE ... WHERE updated_at = $expected` for concurrency control, raise `WorkflowConcurrencyError` on conflict
    - Look up step executor, call it with context and user_input
    - On success: persist step output to `workflow_steps`, merge output into session context, advance `current_step` (or repeat if `_should_repeat_step` returns True)
    - On final step completion: mark session `completed`
    - On step failure: mark step `failed`, preserve prior context, store error in step output
    - On SoundCloud API error: auto-pause session with `paused_reason` in context
    - _Requirements: 1.3, 1.5, 1.6, 1.7, 6.3_

  - [x] 3.3 Implement `skip_step()`, `pause_session()`, `resume_session()`
    - `skip_step()`: validate step is `skippable` via registry, mark step `skipped`, advance to next step
    - `pause_session()`: validate session is `active`, set status to `paused`
    - `resume_session()`: validate session is `paused`, set status to `active`
    - Enforce valid state transitions: active→paused, active→completed, active→failed, paused→active
    - _Requirements: 1.1, 1.4, 2.5_

  - [x] 3.4 Implement `_should_repeat_step()` for repeating steps
    - For `portfolio_critique` / `critique_track`: repeat while `current_track_index < len(track_ids)`
    - For `remediation` / `remediation_step`: repeat while `current_step_index < len(remediation_steps)`
    - _Requirements: 2.1, 3.3_

  - [ ]* 3.5 Write property test: Session lifecycle valid transitions (Property 1)
    - **Property 1: Session lifecycle produces unique IDs and valid state transitions**
    - **Validates: Requirements 1.1, 1.2**
    - Use `hypothesis` with `st.sampled_from(["portfolio_critique", "remediation", "release_planner"])` and random user IDs
    - Verify unique UUIDs, initial status `active`, `current_step` matches first registry step
    - Add to `backend/tests/unit/test_workflow_engine.py`

  - [ ]* 3.6 Write property test: Step ordering maintained (Property 4)
    - **Property 4: Step ordering maintained including skips**
    - **Validates: Requirements 1.6, 2.5**
    - Generate random advance/skip sequences, verify completed/skipped steps form a valid prefix of the registry step sequence
    - Add to `backend/tests/unit/test_workflow_engine.py`

  - [ ]* 3.7 Write property test: Session list filtering (Property 15)
    - **Property 15: Session list filtering by status**
    - **Validates: Requirements 6.4**
    - Generate random session lists with mixed statuses, verify filtering returns only matching sessions
    - Add to `backend/tests/unit/test_workflow_engine.py`

- [x] 4. Checkpoint — Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 5. Implement Health Score calculator
  - [x] 5.1 Create `backend/src/workflow/health.py` with `HealthScoreResult` dataclass and `compute_health_score()` function
    - Implement weighted composite: engagement rate (25%), catalog diversity (20%), release cadence (20%), trend momentum (20%), incident severity (15%)
    - Apply normalization rules from the design for each component
    - Handle missing components: exclude from both numerator and denominator, track in `missing_components` list
    - Return integer score in [0, 100]
    - _Requirements: 5.1, 5.3, 5.5_

  - [x] 5.2 Implement significant change detection
    - Compare consecutive scores; flag as significant when absolute difference > 10 points
    - _Requirements: 5.4_

  - [ ]* 5.3 Write property test: Health score range and weighting (Property 12)
    - **Property 12: Health score range and correct weighting**
    - **Validates: Requirements 5.1**
    - Generate random floats for each component, verify score is integer in [0, 100] and matches weighted sum formula
    - Add to `backend/tests/unit/test_health_score.py`

  - [ ]* 5.4 Write property test: Partial score with missing components (Property 14)
    - **Property 14: Partial health score with missing components**
    - **Validates: Requirements 5.5**
    - Generate random subsets of components, verify re-normalized weighting and `missing_components` list accuracy
    - Add to `backend/tests/unit/test_health_score.py`

  - [ ]* 5.5 Write property test: Significant change detection (Property 13)
    - **Property 13: Significant health score change detection**
    - **Validates: Requirements 5.4**
    - Generate random score pairs, verify flagging when |diff| > 10
    - Add to `backend/tests/unit/test_health_score.py`

- [x] 6. Implement step executors
  - [x] 6.1 Create `backend/src/workflow/steps/__init__.py` and `backend/src/workflow/steps/critique.py`
    - Implement `fetch_tracks_step()`: call `soundcloud.fetch_tracks()`, store track IDs and metadata in context, set `current_track_index = 0`
    - Implement `critique_track_step()`: send current track + catalog metrics to Gemini, return structured critique with strength/weakness/diagnosis/recommendation fields
    - Implement `portfolio_summary_step()`: send all critiques to Gemini for cross-catalog pattern analysis
    - _Requirements: 2.1, 2.2, 2.3, 2.4_

  - [x] 6.2 Create `backend/src/workflow/steps/remediation.py`
    - Implement `load_incident_step()`: load incident context, generate type-specific remediation step list with action/expected_impact fields
    - Implement `remediation_step_step()`: present current action, accept completed/skipped from user input, increment `current_step_index`
    - Implement `verify_outcome_step()`: re-run `run_triage()` on current data, compare to pre-metrics, persist outcome to `remediation_outcomes` table
    - _Requirements: 3.2, 3.3, 3.4, 3.5, 3.6_

  - [x] 6.3 Create `backend/src/workflow/steps/planner.py`
    - Implement `load_context_step()`: load trends, era fingerprint, catalog metrics from existing analytics tools
    - Implement `timing_step()`: send timing data to Gemini, accept user override
    - Implement `style_step()`: send genre/style data to Gemini, accept user override
    - Implement `promotion_step()`: send growth data to Gemini, accept user override
    - Implement `compile_plan_step()`: assemble all recommendations (with overrides) into final release plan
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6_

  - [ ]* 6.4 Write property test: Critique output structure (Property 5)
    - **Property 5: Critique step produces structured output with required fields**
    - **Validates: Requirements 2.2, 2.3**
    - Generate random track metadata, verify output contains non-empty strength, weakness, diagnosis, recommendation
    - Add to `backend/tests/unit/test_workflow_steps.py`

  - [ ]* 6.5 Write property test: Remediation severity gating (Property 6)
    - **Property 6: Remediation launch gating by severity**
    - **Validates: Requirements 3.1**
    - Use `st.sampled_from(Severity)`, verify only critical/warning incidents can launch remediation
    - Add to `backend/tests/unit/test_workflow_steps.py`

  - [ ]* 6.6 Write property test: Incident context and type-specific steps (Property 7)
    - **Property 7: Incident context initialization and type-specific remediation steps**
    - **Validates: Requirements 3.2, 3.3, 3.4**
    - Generate random incidents with valid fields, verify context contains required fields and different incident types produce different remediation step lists
    - Add to `backend/tests/unit/test_workflow_steps.py`

  - [ ]* 6.7 Write property test: Remediation outcome validity (Property 8)
    - **Property 8: Remediation outcome is valid and linked**
    - **Validates: Requirements 3.6**
    - Verify outcome is one of resolved/partially_resolved/unresolved and references correct session_id and incident_type
    - Add to `backend/tests/unit/test_workflow_steps.py`

  - [ ]* 6.8 Write property test: Release planner context (Property 9)
    - **Property 9: Release planner context contains required historical data**
    - **Validates: Requirements 4.1**
    - Generate random trend/era data, verify context contains required fields within valid ranges
    - Add to `backend/tests/unit/test_workflow_steps.py`

  - [ ]* 6.9 Write property test: Release plan completeness (Property 10)
    - **Property 10: Completed release plan contains all sections**
    - **Validates: Requirements 4.5**
    - Generate random recommendation dicts, verify final plan has timing, style, promotion sections each with rationale
    - Add to `backend/tests/unit/test_workflow_steps.py`

  - [ ]* 6.10 Write property test: Override propagation (Property 11)
    - **Property 11: User overrides propagate to subsequent steps**
    - **Validates: Requirements 4.6**
    - Generate random override values, verify they appear in context under correct override keys
    - Add to `backend/tests/unit/test_workflow_steps.py`

- [x] 7. Checkpoint — Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 8. Implement API routes and auth gating
  - [x] 8.1 Add `require_pro` dependency to `backend/src/api/auth.py`
    - Wrap `get_current_user`, check `tier in ("pro", "enterprise")`, raise `TierRestrictionError` (HTTP 403) otherwise
    - _Requirements: 6.6, 6.7_

  - [x] 8.2 Create `backend/src/api/routes/workflows.py` with all workflow endpoints
    - `POST /workflows` — create session via engine
    - `GET /workflows` — list sessions with optional status filter
    - `GET /workflows/{session_id}` — get session state
    - `POST /workflows/{session_id}/advance` — advance with user input
    - `POST /workflows/{session_id}/skip` — skip current step
    - `POST /workflows/{session_id}/pause` — pause session
    - `POST /workflows/{session_id}/resume` — resume session
    - `GET /workflows/health-score/history` — health score time series
    - All endpoints use `Depends(require_pro)`
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6_

  - [x] 8.3 Register workflows router in `backend/src/api/app.py`
    - Import and include the workflows router
    - _Requirements: 6.1_

  - [ ]* 8.4 Write property test: Pro tier gating (Property 16)
    - **Property 16: Pro tier gating returns 403 for non-Pro users**
    - **Validates: Requirements 6.6, 6.7**
    - Use `st.sampled_from(["free", "pro", "enterprise"])`, verify free returns 403, pro/enterprise do not
    - Add to `backend/tests/unit/test_workflow_routes.py`

  - [ ]* 8.5 Write property test: Pause/resume round-trip (Property 2)
    - **Property 2: Pause/resume round-trip preserves context**
    - **Validates: Requirements 1.4**
    - Generate random JSONB context dicts, verify context is identical after pause+resume
    - Add to `backend/tests/unit/test_workflow_engine.py`

  - [ ]* 8.6 Write property test: Step failure preserves state (Property 3)
    - **Property 3: Step failure preserves prior valid state**
    - **Validates: Requirements 1.5**
    - Generate random contexts, simulate step failures, verify context unchanged and step marked failed
    - Add to `backend/tests/unit/test_workflow_engine.py`

- [x] 9. Checkpoint — Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 10. Implement frontend TypeScript types and API proxy routes
  - [x] 10.1 Add workflow TypeScript types to `app/dashboard/types.ts`
    - Add `WorkflowStatus`, `StepStatus`, `RemediationOutcome` enums/unions
    - Add `WorkflowStep`, `WorkflowSession`, `WorkflowListData`, `HealthScorePoint`, `HealthScoreHistory` interfaces
    - _Requirements: 6.2, 7.1_

  - [x] 10.2 Create Next.js API proxy routes for workflows
    - `app/api/workflows/route.ts` — proxy GET (list) and POST (create) to backend
    - `app/api/workflows/[id]/route.ts` — proxy GET (session detail)
    - `app/api/workflows/[id]/advance/route.ts` — proxy POST
    - `app/api/workflows/[id]/skip/route.ts` — proxy POST
    - `app/api/workflows/[id]/pause/route.ts` — proxy POST
    - `app/api/workflows/[id]/resume/route.ts` — proxy POST
    - `app/api/health-score/route.ts` — proxy GET (history)
    - All routes read `cybaop_token` cookie and forward via `backendFetch`
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5_

- [x] 11. Implement frontend components
  - [x] 11.1 Create `app/dashboard/components/workflow-step-list.tsx`
    - Vertical step sequence with status dots (pending/active/completed/failed/skipped)
    - Use color-coded dots: lime=completed, amber=active, rose=failed, sky=skipped, muted=pending
    - Monospace font for step labels and status text
    - _Requirements: 7.1, 7.2, 7.6_

  - [x] 11.2 Create `app/dashboard/components/health-score-display.tsx`
    - Prominent numeric readout (0–100) with color gradient (rose→amber→lime)
    - Trend sparkline showing last 10 computed values
    - Missing components indicator
    - Monospace font for score and component values
    - _Requirements: 7.4_

  - [x] 11.3 Create `app/dashboard/components/critique-panel.tsx`
    - Structured panel with labeled sections: strength, weakness, diagnosis, recommendation
    - Monospace font for data displays
    - Uses existing surface/border color palette
    - _Requirements: 7.3_

  - [x] 11.4 Create `app/dashboard/components/remediation-checklist.tsx`
    - Checklist with action items, expected impact, and completion status
    - Inline metric comparisons (before/after threshold values)
    - Uses existing triage incident card styling patterns
    - _Requirements: 7.5_

- [x] 12. Implement frontend pages
  - [x] 12.1 Create `app/dashboard/workflows/page.tsx` — Workflows list page
    - Fetch sessions via `/api/workflows` and health score via `/api/health-score`
    - Display health score prominently using `health-score-display` component
    - List active/paused/completed sessions with status badges
    - Buttons to create new workflows (portfolio critique, remediation, release planner)
    - Pro tier gating: show upgrade prompt for free users
    - _Requirements: 6.4, 7.4, 7.7_

  - [x] 12.2 Create `app/dashboard/workflows/[id]/page.tsx` — Workflow detail page
    - Fetch session via `/api/workflows/[id]`
    - Render step sequence using `workflow-step-list` component
    - Expand current step with appropriate panel (critique-panel, remediation-checklist, or generic)
    - Advance/skip/pause/resume action buttons based on session state
    - Progress indicator with step name and elapsed time during processing
    - _Requirements: 7.1, 7.2, 7.3, 7.5, 7.6_

- [x] 13. Integrate navigation and wire everything together
  - [x] 13.1 Add "Workflows" tab to navigation in `app/dashboard/components/nav.tsx`
    - Add `{ href: "/dashboard/workflows", label: "Workflows", icon: "⚙️" }` to the `tabs` array
    - Tab appears in both TopNav and BottomNav
    - _Requirements: 7.7_

  - [x] 13.2 Wire step executors to engine via executor lookup map
    - Create a mapping from step names to executor functions in the engine
    - Ensure `advance_session` dispatches to the correct executor based on `current_step`
    - _Requirements: 1.6, 2.1, 3.2, 4.1_

- [x] 14. Final checkpoint — Ensure all tests pass
  - Ensure all existing 48 tests continue passing alongside new tests.
  - Run `PYTHONPATH=backend python3.11 -m pytest backend/tests/unit/ -x -q`
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties from the design document
- Unit tests validate specific examples and edge cases
- All 48 existing tests must continue passing throughout implementation
- Backend uses Python 3.11, asyncpg, Pydantic v2, structlog — no ORM
- Frontend uses Next.js 15 App Router, Tailwind v4, all calls through `lib/fetch.ts`
- Build uses `--no-lint` flag; recharts formatter types must use `any`
