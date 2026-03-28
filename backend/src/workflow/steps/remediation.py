"""Remediation Pipeline step executors — load incident, guide actions, verify outcome."""

from src.shared.errors import WorkflowStateError
from src.shared.logging import get_logger
from src.tools.triage import run_triage

logger = get_logger("workflow.steps.remediation")

# Type-specific remediation step lists
REMEDIATION_STEPS: dict[str, list[dict]] = {
    "play_decay": [
        {
            "action": "Repost the track to re-surface in follower feeds",
            "expected_impact": "Immediate visibility boost",
            "status": "pending",
        },
        {
            "action": "Share on social media with fresh context",
            "expected_impact": "External traffic spike",
            "status": "pending",
        },
        {
            "action": "Add to a curated playlist",
            "expected_impact": "Sustained discovery",
            "status": "pending",
        },
    ],
    "engagement_drop": [
        {
            "action": "Update track description with a call to action",
            "expected_impact": "Higher comment and like conversion",
            "status": "pending",
        },
        {
            "action": "Pin a comment asking listeners for feedback",
            "expected_impact": "Increased comment activity",
            "status": "pending",
        },
        {
            "action": "Cross-promote with a related track in your catalog",
            "expected_impact": "Audience re-engagement",
            "status": "pending",
        },
    ],
    "stale_catalog": [
        {
            "action": "Upload a new track or remix",
            "expected_impact": "Algorithm re-activation",
            "status": "pending",
        },
        {
            "action": "Repost an older track with updated context",
            "expected_impact": "Signal activity to the platform",
            "status": "pending",
        },
    ],
    "concentration_risk": [
        {
            "action": "Promote underperforming tracks via playlists",
            "expected_impact": "Diversified play distribution",
            "status": "pending",
        },
        {
            "action": "Create a playlist featuring deep cuts",
            "expected_impact": "Listener discovery of full catalog",
            "status": "pending",
        },
        {
            "action": "Cross-link tracks in descriptions",
            "expected_impact": "Internal traffic redistribution",
            "status": "pending",
        },
    ],
    "underperformer": [
        {
            "action": "Review and update tags and genre metadata",
            "expected_impact": "Improved discoverability",
            "status": "pending",
        },
        {
            "action": "Update artwork to be more eye-catching",
            "expected_impact": "Higher click-through rate",
            "status": "pending",
        },
        {
            "action": "Share the track with a fresh narrative on socials",
            "expected_impact": "New audience exposure",
            "status": "pending",
        },
    ],
    "silent_track": [
        {
            "action": "Verify track visibility settings are public",
            "expected_impact": "Basic discoverability restored",
            "status": "pending",
        },
        {
            "action": "Add genre, tags, and a description",
            "expected_impact": "Search and recommendation eligibility",
            "status": "pending",
        },
        {
            "action": "Share on socials to seed initial plays",
            "expected_impact": "Bootstrap play count",
            "status": "pending",
        },
    ],
}


VALID_SEVERITIES = {"critical", "warning"}


async def load_incident_step(context: dict, user_input: dict | None = None) -> dict:
    """Load incident context from params and generate type-specific remediation steps."""
    params = context.get("params", {})
    incident_type = params.get("incident_type", "")
    severity = params.get("severity", "")
    affected_track_id = params.get("affected_track_id", "")
    affected_track_title = params.get("affected_track_title", "")
    metric_value = params.get("metric_value", 0.0)
    threshold = params.get("threshold", 0.0)

    # Validate severity gating
    if severity not in VALID_SEVERITIES:
        raise WorkflowStateError(
            f"Remediation requires severity 'critical' or 'warning', got '{severity}'"
        )

    # Get type-specific remediation steps
    steps = REMEDIATION_STEPS.get(incident_type)
    if not steps:
        raise WorkflowStateError(f"Unknown incident type: {incident_type}")

    # Deep copy so we don't mutate the template
    remediation_steps = [dict(s) for s in steps]

    # Capture pre-metrics for later comparison
    pre_metrics = {
        "metric_value": metric_value,
        "threshold": threshold,
    }

    logger.info(
        "incident_loaded",
        incident_type=incident_type,
        severity=severity,
        affected_track_id=affected_track_id,
        steps_count=len(remediation_steps),
    )

    return {
        "incident_type": incident_type,
        "incident_severity": severity,
        "affected_track_id": affected_track_id,
        "affected_track_title": affected_track_title,
        "metric_value": metric_value,
        "threshold": threshold,
        "remediation_steps": remediation_steps,
        "current_step_index": 0,
        "pre_metrics": pre_metrics,
    }


async def remediation_step_step(context: dict, user_input: dict | None = None) -> dict:
    """Present current remediation action, accept completed/skipped from user."""
    remediation_steps = [dict(s) for s in context.get("remediation_steps", [])]
    current_index = context.get("current_step_index", 0)

    if current_index >= len(remediation_steps):
        raise WorkflowStateError("No more remediation steps to process")

    # Determine action from user input
    action = "completed"
    if user_input:
        action = user_input.get("action", "completed")

    if action not in ("completed", "skipped"):
        action = "completed"

    # Update the current step status
    remediation_steps[current_index]["status"] = action

    logger.info(
        "remediation_step_processed",
        index=current_index,
        action=action,
        step_action=remediation_steps[current_index]["action"],
    )

    return {
        "remediation_steps": remediation_steps,
        "current_step_index": current_index + 1,
    }


async def verify_outcome_step(context: dict, user_input: dict | None = None) -> dict:
    """Re-run triage check on current data and compare to pre-metrics."""
    from src.db.queries import get_user_token
    from src.tools.soundcloud import fetch_tracks

    pre_metrics = context.get("pre_metrics", {})
    user_id = context.get("user_id")
    affected_track_id = context.get("affected_track_id")

    # Fetch current track data for triage
    post_metrics: dict = {}
    outcome = "unresolved"

    try:
        token = await get_user_token(user_id) if user_id else None
        if token:
            tracks = await fetch_tracks(token)
            report = run_triage(tracks)

            # Find if the affected track still has an incident
            affected_incidents = [
                i for i in report.incidents
                if i.track_id == affected_track_id
            ]

            post_metrics = {
                "incident_count": report.incident_count,
                "critical_count": report.critical_count,
                "warning_count": report.warning_count,
                "catalog_uptime": report.catalog_uptime,
            }

            # Determine outcome
            incident_type = context.get("incident_type")
            matching = [
                i for i in affected_incidents
                if i.incident_type.value == incident_type
            ]

            if not matching:
                outcome = "resolved"
            elif all(i.severity.value == "info" for i in matching):
                outcome = "partially_resolved"
            else:
                outcome = "unresolved"
        else:
            post_metrics = {"error": "Could not fetch current data"}
    except Exception as exc:
        logger.warning("verify_outcome_error", error=str(exc))
        post_metrics = {"error": str(exc)}

    logger.info(
        "outcome_verified",
        outcome=outcome,
        affected_track_id=affected_track_id,
    )

    return {
        "post_metrics": post_metrics,
        "outcome": outcome,
    }
