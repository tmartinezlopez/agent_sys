## Purpose

Define the implementation stage that consumes a validated OpenSpec change,
applies its approved tasks in a writable checkout, and leaves evidence for
testing and review.

## ADDED Requirements

### Requirement: Consume a validated spec-writer handoff

The `implementer` stage SHALL consume the OpenSpec change and artefact paths
recorded by `spec-writer` and SHALL refuse to operate without a valid handoff.

#### Scenario: Handoff is available

- **WHEN** the previous stage is `passed` and its result references a valid
  OpenSpec change
- **THEN** the implementer receives that change name, objective and tasks path
- **AND** it works in the declared writable checkout

#### Scenario: Handoff is missing or invalid

- **WHEN** the previous stage is not `passed` or a referenced artefact is absent
- **THEN** the implementer is marked `blocked` or `failed`
- **AND** it does not modify the checkout

### Requirement: Apply only approved tasks

The stage SHALL instruct Codex to implement the tasks from the handoff and
SHALL persist the files changed and the final implementation summary.

#### Scenario: Tasks are implemented

- **WHEN** Codex completes successfully in the writable checkout
- **THEN** the stage records its stdout, changed-file evidence and result
- **AND** the next stage can locate the implementation from disk

#### Scenario: Codex fails during implementation

- **WHEN** Codex exits non-zero, times out or cannot start
- **THEN** the stage is `failed`
- **AND** no later stage is launched

### Requirement: Validate the implementation handoff

The stage SHALL verify that the OpenSpec change remains structurally valid
after implementation before reporting success.

#### Scenario: Post-implementation validation passes

- **WHEN** the implementation process succeeds and strict OpenSpec validation
  succeeds
- **THEN** the stage reports `passed` and records validation evidence

#### Scenario: Post-implementation validation fails

- **WHEN** strict validation fails after implementation
- **THEN** the stage reports `failed`
- **AND** the validation output explains why the pipeline stopped
