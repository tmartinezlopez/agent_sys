## Purpose

Define the shared execution contract that lets six real Codex roles run as
ordered, observable pipeline stages without depending on implicit process
memory or unsafe tmux side effects.

## ADDED Requirements

### Requirement: Canonical role catalog

The system SHALL define the six pipeline roles `spec-writer`, `implementer`,
`test-runner`, `reviewer`, `ui-reviewer` and `qa`, with an explicit canonical
order and per-role model, reasoning effort, sandbox mode, prompt contract,
timeout and retry policy.

#### Scenario: Every canonical role has a concrete configuration

- **WHEN** the coordinator loads the role catalog
- **THEN** it finds all six roles with non-empty model, reasoning, sandbox and
  prompt-contract values
- **AND** it does not create or select an unspecified generic role

#### Scenario: The canonical order is deterministic

- **WHEN** the coordinator evaluates the next stage
- **THEN** it uses `spec-writer`, `implementer`, `test-runner`, `reviewer`,
  optional `ui-reviewer`, `qa` in that order

### Requirement: Persistent run and stage state

The system SHALL persist each run with a stable `run_id`, stage status,
timestamps, exit code, result-artifact references and append-only events using
the states `pending`, `running`, `passed`, `failed` and `blocked`.

#### Scenario: A stage transition is recoverable

- **WHEN** the coordinator process stops after recording a stage event
- **THEN** a new coordinator process can reconstruct the run and stage status
  from persisted files without relying on in-memory state

#### Scenario: Invalid advancement is rejected

- **WHEN** a stage is requested while its predecessor is not `passed` or an
  explicitly approved gate is missing
- **THEN** the coordinator does not launch the requested stage and records the
  reason as a blocked transition

### Requirement: Explicit Codex launch contract

The system SHALL launch each stage as an external `codex exec` process using
the role's concrete model, reasoning configuration, sandbox, working
directory and prompt, and SHALL persist the exact command metadata without
using the OpenAI API.

#### Scenario: A role command is auditable

- **WHEN** a stage starts
- **THEN** the run records the selected role, model, sandbox, working directory
  and exact process arguments before launching Codex

#### Scenario: A process failure is terminal for the stage

- **WHEN** Codex exits with a non-zero code, cannot start or exceeds its timeout
- **THEN** the stage is marked `failed`, its stdout/stderr are persisted and
  no successor stage is launched

### Requirement: Owned named tmux targets

The system SHALL run stages in a project-owned tmux session using named windows
and SHALL verify session/window ownership before creating, observing or
stopping a process.

#### Scenario: The coordinator creates an owned stage window

- **WHEN** a stage is launched and the project session is absent
- **THEN** the coordinator creates the session and a named window for that
  stage without using a numeric window index

#### Scenario: An unrelated tmux session is protected

- **WHEN** a requested session or window does not match the coordinator's
  project/run ownership metadata
- **THEN** the coordinator does not kill, rename or attach to that target and
  records a failed or blocked operation

### Requirement: Verifiable stage artefacts

The system SHALL persist each stage's prompt, stdout, stderr, result metadata
and role-specific artefact references under its run directory.

#### Scenario: A successful stage exposes its result

- **WHEN** a role process exits with code zero and produces its required output
- **THEN** the coordinator marks the stage `passed` and records the output path
  in the run state and event ledger

#### Scenario: A missing required artefact prevents advancement

- **WHEN** a role exits successfully but its required artefact is absent or
  invalid
- **THEN** the coordinator marks the stage `failed` or `blocked` according to
  the contract and does not launch the next stage
