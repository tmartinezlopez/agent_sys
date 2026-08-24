## Why

The target is a faithful, incremental adaptation of `rburgosm/agentic-system`
to external Codex CLI processes, not a collection of isolated agent demos. The
repository needs one coherent architecture and dependency-ordered backlog
before runtime or role implementation starts.

## What Changes

- Document the complete operator → coordinator → tmux → pipeline → role flow.
- Define the six real roles, their order and the boundaries between role
  contracts and runtime mechanics.
- Define the persistent run, stage, event, gate and artefact concepts.
- Define the dependency-ordered implementation backlog from bootstrap through
  observability and recovery.
- Define completion criteria for each backlog stage so the next stage is only
  started after its prerequisite is verifiable.
- Record Git/worktree setup as an infrastructure prerequisite without silently
  initialising or overwriting the current directory.

## Capabilities

### New Capabilities

- `system-architecture`: Observable system boundaries, roles, pipeline order,
  artefacts, gates and implementation dependencies.

### Modified Capabilities

<!-- No existing OpenSpec capabilities exist yet. -->

## Impact

- Adds architecture and backlog documentation for the Python/Bash project.
- Aligns the existing pipeline contract with the final six-role design.
- Does not launch Codex, create tmux sessions or modify production code.
- Provides the scope and order for the subsequent runtime and role changes.
