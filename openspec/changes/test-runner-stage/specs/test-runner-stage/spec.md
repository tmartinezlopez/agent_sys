## Purpose

Define the read-only testing stage that executes the project's declared tests
after implementation and produces evidence for review.

## ADDED Requirements

### Requirement: Consume an implementation handoff

The `test-runner` stage SHALL run only after `implementer` is passed and SHALL
use the checkout and evidence referenced by that stage.

#### Scenario: Valid implementation is available

- **WHEN** implementer is passed and its checkout reference exists
- **THEN** test-runner receives the implementation context and starts in
  read-only mode

#### Scenario: Implementation handoff is unavailable

- **WHEN** implementer is not passed or its checkout cannot be located
- **THEN** test-runner is blocked and no test process is launched

### Requirement: Execute declared project tests

The stage SHALL execute the project's configured test command without modifying
source files and SHALL persist the exact command and outputs.

#### Scenario: Tests pass

- **WHEN** the declared test command exits with code zero
- **THEN** the stage reports `passed` and records stdout, stderr and exit code

#### Scenario: Tests fail

- **WHEN** the test command exits non-zero or times out
- **THEN** the stage reports `failed`
- **AND** the pipeline does not launch the reviewer

### Requirement: Produce review evidence

The stage SHALL persist a machine-readable summary of the test command, result,
duration and relevant output paths for later review and QA.

#### Scenario: Reviewer consumes test evidence

- **WHEN** test-runner finishes
- **THEN** its result references the test summary and raw logs from disk
- **AND** no conversational memory is required
