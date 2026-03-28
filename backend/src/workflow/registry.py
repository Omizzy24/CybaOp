"""Workflow Registry — step definitions and lookup for all workflow types."""

from dataclasses import dataclass


@dataclass(frozen=True)
class StepDefinition:
    name: str
    label: str
    requires_input: bool = False
    skippable: bool = False


WORKFLOW_TYPES: dict[str, list[StepDefinition]] = {
    "portfolio_critique": [
        StepDefinition("fetch_tracks", "Fetching catalog"),
        StepDefinition("critique_track", "Analyzing track", requires_input=False, skippable=True),
        StepDefinition("portfolio_summary", "Generating portfolio summary"),
    ],
    "remediation": [
        StepDefinition("load_incident", "Loading incident context"),
        StepDefinition("remediation_step", "Remediation action", requires_input=True, skippable=True),
        StepDefinition("verify_outcome", "Verifying improvement"),
    ],
    "release_planner": [
        StepDefinition("load_context", "Loading historical data"),
        StepDefinition("timing_recommendation", "Analyzing release timing", requires_input=True),
        StepDefinition("style_recommendation", "Analyzing genre & style", requires_input=True),
        StepDefinition("promotion_strategy", "Building promotion plan", requires_input=True),
        StepDefinition("compile_plan", "Compiling release plan"),
    ],
}


def get_workflow_steps(workflow_type: str) -> list[StepDefinition]:
    steps = WORKFLOW_TYPES.get(workflow_type)
    if not steps:
        raise ValueError(f"Unknown workflow type: {workflow_type}")
    return steps


def get_step_definition(workflow_type: str, step_name: str) -> StepDefinition:
    for step in get_workflow_steps(workflow_type):
        if step.name == step_name:
            return step
    raise ValueError(f"Unknown step {step_name} for {workflow_type}")
