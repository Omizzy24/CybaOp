---
inclusion: manual
---

# Agent Builder

When I ask you to "build me an agent for X", follow this process:

## Step 1: Identify the Domain
- What area does this agent operate in? (coding, debugging, research, deployment, etc.)
- What tools/APIs does it need access to?
- What's the expected input and output?

## Step 2: Generate the Agent Definition
Output a complete agent definition with:

### System Prompt
- Role and expertise area
- Core rules (what to do, what NOT to do)
- Domain-specific knowledge and constraints
- Output format requirements
- Failure mode protections (when to stop and ask vs proceed)

### Steering File
- If the agent is for a recurring workflow, generate a `.kiro/steering/` file
- Include `inclusion: manual` in frontmatter so it's opt-in
- Keep it focused — one agent, one job

### Usage Pattern
- Example input format
- Example output
- When to use this agent vs general chat

## Step 3: Validate
- Does the agent have enough context to avoid hallucination?
- Are there clear boundaries on what it should NOT do?
- Is the output format specific enough to be immediately useful?

## Quality Criteria
- Grounded: references real files, APIs, conventions from the project
- Bounded: clear scope, won't drift into unrelated work
- Actionable: outputs are directly usable, not theoretical
- Failure-aware: knows when to stop and ask for clarification
