# Requirements Document

## Introduction

CybaOp must scale from its current single-digit concurrency ceiling to support 1000+ concurrent users in production. This feature addresses ten bottlenecks identified across the backend (FastAPI/asyncpg), frontend (Next.js), and infrastructure (Neon Postgres, in-memory state). The changes span database connection pooling, LLM concurrency control, async step execution, background job scheduling, pagination, singleton lifecycle management, Redis-backed state, frontend data caching, session archival, and client-side retry logic.

## Glossary

- **Connection_Pool**: The asyncpg connection pool managed in `backend/src/db/session.py`, currently hard-coded to `max_size=5`.
- **LLM_Semaphore**: An `asyncio.Semaphore` that caps the number of concurrent Gemini LLM calls across all workflow step executors.
- **Workflow_Engine**: The `WorkflowEngine` class in `backend/src/workflow/engine.py` that manages session lifecycle and step execution.
- **Step_Executor**: An async callable registered with the Workflow_Engine that performs a single workflow step (e.g., `critique_track_step`, `timing_step`).
- **Rate_Limiter**: The `RateLimiterMiddleware` in `backend/src/api/middleware/rate_limiter.py` that enforces per-user request limits using a sliding window.
- **Health_Score_Scheduler**: A background task that computes health scores on a periodic schedule rather than inline during API requests.
- **Session_List_API**: The `list_sessions` method on Workflow_Engine and the `GET /workflows` route that returns workflow sessions for a user.
- **Redis_Store**: A Redis instance used for persistent rate-limiting state, cached health scores, and other frequently-accessed data.
- **Frontend_Cache**: An SWR or React Query caching layer on the Next.js frontend that reduces redundant API calls on navigation.
- **Session_Archiver**: A background process that moves completed workflow session JSONB context data to cold storage after 30 days.
- **Advance_Endpoint**: The `POST /workflows/{session_id}/advance` route that executes the current workflow step.
- **Settings**: The `Settings` Pydantic model in `backend/src/shared/config.py` that loads configuration from environment variables.

## Requirements

### Requirement 1: Configurable Database Connection Pool

**User Story:** As a platform operator, I want the database connection pool size to be configurable via environment variables, so that I can tune pool sizing for production load without code changes.

#### Acceptance Criteria

1. THE Settings SHALL expose `db_pool_min_size` and `db_pool_max_size` fields with defaults of 2 and 5 respectively.
2. WHEN the Connection_Pool is created, THE Connection_Pool SHALL use the `db_pool_min_size` and `db_pool_max_size` values from Settings.
3. WHEN `db_pool_max_size` is set to a value between 10 and 20 in the environment, THE Connection_Pool SHALL create a pool with that maximum size.
4. IF `db_pool_max_size` is set to a value less than `db_pool_min_size`, THEN THE Settings SHALL raise a validation error at startup.

### Requirement 2: LLM Concurrency Control

**User Story:** As a platform operator, I want concurrent Gemini LLM calls to be capped with a semaphore, so that CybaOp does not exceed Google's rate limits under load.

#### Acceptance Criteria

1. THE Settings SHALL expose an `llm_max_concurrency` field with a default of 5.
2. WHEN a Step_Executor calls Gemini, THE LLM_Semaphore SHALL limit the number of concurrent in-flight LLM calls to the configured `llm_max_concurrency` value.
3. WHEN the LLM_Semaphore is fully acquired, THE next LLM call SHALL wait until a slot is released rather than failing immediately.
4. IF an LLM call raises an exception while holding the LLM_Semaphore, THEN THE LLM_Semaphore SHALL release the slot so other calls can proceed.

### Requirement 3: Async Step Execution with Background Tasks

**User Story:** As a user, I want the advance endpoint to return immediately while the step runs in the background, so that long-running LLM calls do not block the HTTP response.

#### Acceptance Criteria

1. WHEN a client sends a POST to the Advance_Endpoint, THE Advance_Endpoint SHALL return an HTTP 202 Accepted response with the session in an "advancing" or "active" state within 500ms.
2. WHEN the Advance_Endpoint returns 202, THE Workflow_Engine SHALL execute the current step in a background task.
3. WHEN the background step execution completes successfully, THE Workflow_Engine SHALL update the session state and step output in the database.
4. IF the background step execution fails, THEN THE Workflow_Engine SHALL mark the step as failed and log the error.
5. WHEN a client polls `GET /workflows/{session_id}`, THE Workflow_Engine SHALL return the current session state including any step that completed in the background.

### Requirement 4: Health Score Background Scheduling

**User Story:** As a platform operator, I want health scores to be computed on a background schedule, so that analytics requests do not trigger expensive inline computation at scale.

#### Acceptance Criteria

1. THE Health_Score_Scheduler SHALL compute health scores for active users on a configurable interval with a default of 60 minutes.
2. THE Settings SHALL expose a `health_score_interval_minutes` field with a default of 60.
3. WHEN a client requests a health score, THE health score API SHALL return the most recently cached score from the database rather than computing inline.
4. WHEN the Health_Score_Scheduler completes a computation cycle, THE Health_Score_Scheduler SHALL store the results in the `health_scores` table.

### Requirement 5: Session List Pagination

**User Story:** As a user with many workflow sessions, I want the session list to be paginated, so that the API returns results efficiently without loading all sessions at once.

#### Acceptance Criteria

1. THE Session_List_API SHALL accept an optional `limit` query parameter with a default of 20 and a maximum of 100.
2. THE Session_List_API SHALL accept an optional `cursor` query parameter representing the `created_at` timestamp of the last item on the previous page.
3. WHEN a `cursor` is provided, THE Session_List_API SHALL return only sessions created before the cursor timestamp, ordered by `created_at` descending.
4. THE Session_List_API response SHALL include a `next_cursor` field set to the `created_at` value of the last returned session, or null when no more results exist.
5. WHEN no `cursor` is provided, THE Session_List_API SHALL return the first page of results ordered by `created_at` descending.

### Requirement 6: Singleton Workflow Engine

**User Story:** As a platform operator, I want the WorkflowEngine to be created once at application startup, so that executor registration happens once and per-request overhead is eliminated.

#### Acceptance Criteria

1. WHEN the FastAPI application starts, THE application lifespan SHALL create a single Workflow_Engine instance with all Step_Executors registered.
2. THE workflow route handlers SHALL receive the Workflow_Engine via FastAPI dependency injection rather than creating a new instance per request.
3. THE singleton Workflow_Engine SHALL be the same object instance across all concurrent requests within the same process.

### Requirement 7: Redis-Backed Rate Limiting

**User Story:** As a platform operator, I want rate-limiting state stored in Redis, so that rate limits persist across deploys and are shared across multiple backend instances.

#### Acceptance Criteria

1. THE Settings SHALL expose a `redis_url` field that is optional and defaults to empty string.
2. WHEN `redis_url` is configured, THE Rate_Limiter SHALL store sliding window counters in the Redis_Store instead of in-memory dictionaries.
3. WHEN `redis_url` is not configured, THE Rate_Limiter SHALL fall back to the existing in-memory sliding window implementation.
4. WHEN the Redis_Store is unavailable, THE Rate_Limiter SHALL allow the request through and log a warning rather than rejecting the request.
5. THE Redis-backed Rate_Limiter SHALL produce identical rate-limiting behavior to the in-memory implementation for a single-instance deployment.

### Requirement 8: Redis-Backed Health Score Cache

**User Story:** As a platform operator, I want frequently-accessed health scores cached in Redis, so that repeated reads do not hit the database.

#### Acceptance Criteria

1. WHEN `redis_url` is configured, THE health score API SHALL check the Redis_Store for a cached score before querying the database.
2. WHEN a health score is computed by the Health_Score_Scheduler, THE Health_Score_Scheduler SHALL write the result to both the database and the Redis_Store.
3. THE cached health score in Redis_Store SHALL expire after a configurable TTL with a default of 3600 seconds.
4. WHEN `redis_url` is not configured, THE health score API SHALL read directly from the database.


### Requirement 9: Frontend Data Caching

**User Story:** As a user, I want workflow and analytics data to be cached on the frontend, so that navigating between pages feels instant and reduces unnecessary API calls.

#### Acceptance Criteria

1. WHEN the user navigates to the workflows list page, THE Frontend_Cache SHALL serve stale data immediately while revalidating in the background.
2. WHEN the user navigates back to a previously-visited workflow detail page, THE Frontend_Cache SHALL display the cached session data within 100ms.
3. WHEN a mutation occurs (create, advance, pause, resume, skip), THE Frontend_Cache SHALL invalidate the relevant cached entries and refetch.
4. THE Frontend_Cache SHALL set a stale-while-revalidate window of 30 seconds for workflow list data and 10 seconds for individual session data.

### Requirement 10: Completed Session Archival

**User Story:** As a platform operator, I want completed workflow session contexts archived after 30 days, so that large JSONB columns do not degrade database performance over time.

#### Acceptance Criteria

1. THE Session_Archiver SHALL identify completed workflow sessions where `completed_at` is older than 30 days.
2. WHEN a session is identified for archival, THE Session_Archiver SHALL replace the `context` JSONB column with a minimal stub containing only `{"archived": true, "archived_at": "<timestamp>"}`.
3. THE Session_Archiver SHALL store the original context in a separate `archived_session_contexts` table with a foreign key to the session.
4. WHEN a client requests an archived session via `GET /workflows/{session_id}`, THE Workflow_Engine SHALL return the session with the stub context and an `archived` flag set to true.
5. THE Session_Archiver SHALL run on a configurable schedule with a default interval of 24 hours.

### Requirement 11: Client-Side Retry for Concurrency Conflicts

**User Story:** As a user, I want the frontend to automatically retry when a concurrency conflict occurs, so that optimistic locking failures are handled transparently.

#### Acceptance Criteria

1. WHEN the Advance_Endpoint returns HTTP 409 (concurrency conflict), THE frontend SHALL automatically retry the request up to 3 times with exponential backoff starting at 500ms.
2. WHEN all retry attempts for a 409 response are exhausted, THE frontend SHALL display an error message indicating the workflow was modified by another session.
3. WHEN a retry for a 409 response succeeds, THE frontend SHALL update the displayed session state with the successful response.
4. THE frontend retry logic SHALL apply only to 409 status codes and SHALL NOT retry other 4xx or 5xx errors automatically.
