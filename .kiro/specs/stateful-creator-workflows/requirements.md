# Requirements Document

## Introduction

Stateful Creator Workflows adds multi-step, context-preserving workflow pipelines to CybaOp that bridge SoundCloud catalog data with AI-driven analysis. Instead of one-shot dashboards, creators get guided operational workflows — track-by-track portfolio critiques, automated remediation pipelines triggered by triage incidents, release planning sessions, and portfolio health scoring that evolves over time. These workflows persist state across interactions, remember prior context, and produce actionable outputs. The UI presents these as specialized production tooling: dense, mono-font ops views with opinionated layouts — not generic SaaS chrome.

## Glossary

- **Workflow_Engine**: The backend subsystem that manages workflow lifecycle — creation, step execution, state persistence, and completion. Built on top of the existing LangGraph pipeline infrastructure.
- **Workflow_Session**: A single instance of a running workflow, identified by a unique session ID, with persisted state across steps.
- **Workflow_Step**: An individual stage within a workflow that performs a discrete operation (data fetch, AI analysis, user decision) and advances the session state.
- **Portfolio_Critique**: A workflow type that iterates through a creator's tracks, applying AI analysis to each one and producing per-track assessments with an overall portfolio summary.
- **Remediation_Pipeline**: A workflow type triggered by triage incidents that guides the creator through fixing detected issues with specific, actionable steps.
- **Release_Planner**: A workflow type that uses historical performance data, trend analysis, and catalog gaps to recommend release timing, genre focus, and promotional strategy.
- **Health_Score**: A composite numeric score (0–100) representing overall portfolio health, computed from engagement rates, catalog diversity, release cadence, trend momentum, and incident severity.
- **Ops_View**: A UI presentation mode using monospace fonts, dense information layout, and status-indicator styling — designed to feel like production monitoring tooling rather than a consumer dashboard.
- **Step_Context**: The accumulated state carried forward between workflow steps, including prior AI outputs, user decisions, and intermediate computations.
- **Workflow_Registry**: The backend component that defines available workflow types, their step sequences, and validation rules.

## Requirements

### Requirement 1: Workflow Engine and State Persistence

**User Story:** As a Pro creator, I want my workflows to remember where I left off and what was discussed, so that I can work through multi-step analysis sessions without losing context.

#### Acceptance Criteria

1. THE Workflow_Engine SHALL support creating, resuming, pausing, and completing Workflow_Sessions.
2. WHEN a Workflow_Session is created, THE Workflow_Engine SHALL generate a unique session ID and persist the initial state to the database.
3. WHEN a Workflow_Step completes, THE Workflow_Engine SHALL persist the updated Step_Context to the database within the same transaction as the step result.
4. WHEN a creator resumes a paused Workflow_Session, THE Workflow_Engine SHALL restore the full Step_Context from the most recent persisted state.
5. IF a Workflow_Step fails during execution, THEN THE Workflow_Engine SHALL mark the step as failed, preserve the prior valid state, and allow the creator to retry the failed step.
6. THE Workflow_Engine SHALL enforce that each Workflow_Session progresses through steps in the order defined by the Workflow_Registry for that workflow type.
7. WHILE a Workflow_Session is active, THE Workflow_Engine SHALL reject concurrent step executions on the same session.

### Requirement 2: Portfolio Critique Workflow

**User Story:** As a Pro creator, I want AI to analyze my tracks one by one and give me honest, specific feedback on each, so that I understand what's working and what needs improvement across my catalog.

#### Acceptance Criteria

1. WHEN a Portfolio_Critique workflow is started, THE Workflow_Engine SHALL fetch the creator's current track list from SoundCloud and present them as the critique queue.
2. FOR each track in the critique queue, THE Portfolio_Critique SHALL send track metadata, engagement metrics, and catalog-relative performance to the Gemini LLM for analysis.
3. WHEN the LLM returns a critique for a track, THE Portfolio_Critique SHALL produce a structured assessment containing: a strength summary, a weakness summary, an engagement diagnosis, and a specific improvement recommendation.
4. WHEN all tracks in the queue have been critiqued, THE Portfolio_Critique SHALL generate an overall portfolio summary identifying patterns across the catalog.
5. THE Portfolio_Critique SHALL allow the creator to skip individual tracks without breaking the workflow sequence.
6. IF the SoundCloud API is unreachable during a Portfolio_Critique, THEN THE Workflow_Engine SHALL pause the session and notify the creator that the workflow can be resumed when connectivity is restored.

### Requirement 3: Remediation Pipeline Workflow

**User Story:** As a Pro creator, I want CybaOp to guide me through fixing the issues it detects in triage, so that I get actionable steps instead of just alerts.

#### Acceptance Criteria

1. WHEN a triage incident is detected with severity "critical" or "warning", THE Remediation_Pipeline SHALL be available to launch from that incident.
2. WHEN a Remediation_Pipeline is started from an incident, THE Workflow_Engine SHALL load the incident context (type, severity, affected track, metric values, thresholds) into the initial Step_Context.
3. THE Remediation_Pipeline SHALL present remediation steps specific to the incident type: play_decay, engagement_drop, stale_catalog, concentration_risk, underperformer, or silent_track.
4. FOR each remediation step, THE Remediation_Pipeline SHALL provide a concrete action description, the expected impact, and a way for the creator to mark the step as completed or skipped.
5. WHEN all remediation steps are completed or skipped, THE Remediation_Pipeline SHALL re-run the relevant triage check against current data and report whether the incident has improved.
6. THE Remediation_Pipeline SHALL persist the outcome (resolved, partially_resolved, unresolved) and link it back to the originating incident for historical tracking.

### Requirement 4: Release Planner Workflow

**User Story:** As a Pro creator, I want CybaOp to help me plan my next release using my historical data, so that I can time and position it for maximum impact.

#### Acceptance Criteria

1. WHEN a Release_Planner workflow is started, THE Workflow_Engine SHALL load the creator's trend analysis, era fingerprint, best release day/hour, and catalog gap analysis into the initial Step_Context.
2. THE Release_Planner SHALL present a timing recommendation step that uses historical best_release_day and best_release_hour data to suggest optimal release windows.
3. THE Release_Planner SHALL present a genre/style recommendation step that analyzes the era fingerprint and catalog concentration to suggest what type of track to release next.
4. THE Release_Planner SHALL present a promotion strategy step that uses growth velocity trends and engagement patterns to recommend specific promotional actions.
5. WHEN all planning steps are completed, THE Release_Planner SHALL produce a structured release plan document summarizing timing, style, and promotion recommendations.
6. THE Release_Planner SHALL allow the creator to override any AI recommendation with their own input, and the subsequent steps SHALL incorporate the override into their analysis.

### Requirement 5: Portfolio Health Score

**User Story:** As a Pro creator, I want a single score that tells me how my portfolio is doing overall, so that I can track improvement over time without digging into every metric.

#### Acceptance Criteria

1. THE Workflow_Engine SHALL compute a Health_Score (0–100) from the following weighted components: engagement rate (25%), catalog diversity (20%), release cadence (20%), trend momentum (20%), and incident severity (15%).
2. WHEN analytics are run for a Pro creator, THE Workflow_Engine SHALL compute and persist the Health_Score alongside the analytics snapshot.
3. THE Health_Score SHALL be comparable across time — the same catalog state SHALL produce the same score regardless of when it is computed.
4. WHEN the Health_Score changes by more than 10 points between consecutive computations, THE Workflow_Engine SHALL flag the change as significant and include a brief AI-generated explanation of the primary driver.
5. IF insufficient data exists to compute one or more Health_Score components, THEN THE Workflow_Engine SHALL compute a partial score using available components and indicate which components are missing.

### Requirement 6: Workflow API Endpoints

**User Story:** As a frontend developer, I want clean REST endpoints for all workflow operations, so that the UI can drive workflows without embedding business logic.

#### Acceptance Criteria

1. THE Workflow_Engine SHALL expose a POST endpoint to create a new Workflow_Session, accepting workflow type and optional initial parameters.
2. THE Workflow_Engine SHALL expose a GET endpoint to retrieve the current state of a Workflow_Session, including the current step, Step_Context, and available actions.
3. THE Workflow_Engine SHALL expose a POST endpoint to advance a Workflow_Session to the next step, accepting user input for the current step.
4. THE Workflow_Engine SHALL expose a GET endpoint to list all Workflow_Sessions for the authenticated creator, filterable by status (active, paused, completed).
5. THE Workflow_Engine SHALL expose a GET endpoint to retrieve the creator's Health_Score history as a time series.
6. THE Workflow_Engine SHALL require Pro tier authentication for all workflow endpoints.
7. IF a non-Pro creator attempts to access a workflow endpoint, THEN THE Workflow_Engine SHALL return a 403 response with a message indicating the feature requires Pro.

### Requirement 7: Ops-Style Workflow UI

**User Story:** As a creator, I want the workflow interface to feel like specialized production tooling, so that I trust it as a serious analytical tool rather than a generic AI chatbot.

#### Acceptance Criteria

1. THE Ops_View SHALL use monospace fonts for all data displays, step labels, status indicators, and metric values within workflow screens.
2. THE Ops_View SHALL display workflow progress as a vertical step sequence with status indicators (pending, active, completed, failed, skipped) using color-coded dots consistent with the existing triage severity palette.
3. THE Ops_View SHALL present AI critique output in structured panels with labeled sections (strength, weakness, diagnosis, recommendation) rather than as free-form chat bubbles.
4. THE Ops_View SHALL display the Health_Score as a prominent numeric readout with a trend sparkline showing the last 10 computed values.
5. THE Ops_View SHALL present remediation steps as a checklist with inline metric comparisons (before/after threshold values) using the existing triage incident card styling.
6. WHEN a workflow step is processing, THE Ops_View SHALL display a progress indicator with the step name and elapsed time, consistent with the existing pipeline badge pattern.
7. THE Ops_View SHALL integrate into the existing navigation as a "Workflows" tab in both the TopNav and BottomNav components.

### Requirement 8: Workflow Database Schema

**User Story:** As a backend developer, I want workflow state persisted in Postgres, so that sessions survive server restarts and can be queried for analytics.

#### Acceptance Criteria

1. THE Workflow_Engine SHALL store Workflow_Sessions in a `workflow_sessions` table with columns: id (UUID), user_id (FK to users), workflow_type, status, current_step, context (JSONB), created_at, updated_at, completed_at.
2. THE Workflow_Engine SHALL store individual step results in a `workflow_steps` table with columns: id (UUID), session_id (FK to workflow_sessions), step_name, status, input (JSONB), output (JSONB), started_at, completed_at.
3. THE Workflow_Engine SHALL store Health_Score history in a `health_scores` table with columns: id (UUID), user_id (FK to users), score (INTEGER), components (JSONB), explanation (TEXT), computed_at.
4. THE Workflow_Engine SHALL store remediation outcomes in a `remediation_outcomes` table with columns: id (UUID), session_id (FK to workflow_sessions), incident_type, original_severity, outcome, resolved_at.
5. THE Workflow_Engine SHALL use the existing asyncpg connection pool from `src/db/session.py` for all database operations.
