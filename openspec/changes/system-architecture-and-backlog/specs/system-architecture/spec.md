## Purpose

Provide a single, reviewable architecture and dependency order for the six-role
Codex pipeline so implementation can proceed through verified vertical slices.

## ADDED Requirements

### Requirement: Complete system flow is explicit

The project SHALL document the interaction between the interactive operator,
coordinator, tmux session, pipeline state, external Codex processes, artefacts,
events, gates and recovery mechanisms.

#### Scenario: A new contributor can locate every system boundary

- **WHEN** a contributor reads the architecture document
- **THEN** it identifies who starts a run, who launches stages, where each
  process runs, how results are persisted and how advancement is decided

### Requirement: Six roles and stage order are canonical

The architecture SHALL define `spec-writer`, `implementer`, `test-runner`,
`reviewer`, optional `ui-reviewer` and `qa` as real roles, with their order and
the condition that makes `ui-reviewer` applicable.

#### Scenario: The pipeline order is unambiguous

- **WHEN** implementation work is selected from the backlog
- **THEN** the next role and its predecessor condition can be determined
  without relying on conversation memory

### Requirement: Implementation backlog is dependency ordered

The project SHALL maintain a backlog whose items state prerequisites,
deliverables and verification criteria, covering foundation, runtime, roles,
recovery and operator observability.

#### Scenario: A backlog item cannot hide an unmet prerequisite

- **WHEN** a backlog item is selected
- **THEN** its documented prerequisites and completion evidence identify whether
  it is ready to start

### Requirement: Architecture decisions preserve the reference boundaries

The architecture SHALL keep role contracts separate from runtime mechanics and
SHALL identify adaptations required because Codex roles are external processes
rather than Claude native subagents.

#### Scenario: A role contract is portable across launch contexts

- **WHEN** the tmux transport is changed or tested independently
- **THEN** the role's model, permissions, prompt, inputs and outputs remain
  defined by its role contract rather than hidden in the launcher

### Requirement: Infrastructure prerequisites are explicit

The backlog SHALL identify Git repository/worktree availability, OpenSpec,
Codex CLI authentication and tmux as prerequisites without silently changing
the user's existing directory or external sessions.

#### Scenario: Missing infrastructure stops only dependent work

- **WHEN** a prerequisite is unavailable
- **THEN** the affected backlog item is marked blocked with the exact diagnosis
  and unrelated read-only design work remains valid
