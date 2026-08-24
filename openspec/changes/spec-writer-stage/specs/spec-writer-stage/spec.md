## Purpose

Define the real first pipeline role that turns an objective into a validated
OpenSpec change and leaves explicit artefacts for later implementation stages.

## ADDED Requirements

### Requirement: Create a concrete OpenSpec change

The `spec-writer` stage SHALL create an OpenSpec change from the run objective
using the repository's configured workflow and SHALL not select a generic role
or fabricate a substitute specification.

#### Scenario: A valid change is produced

- **WHEN** the stage receives a valid objective and a writable project checkout
- **THEN** it creates a named OpenSpec change with proposal, spec, design and
  tasks artefacts
- **AND** it records the change name in its result artefact

#### Scenario: Invalid objective stops the stage

- **WHEN** the objective is empty or cannot be converted into a valid change
- **THEN** the stage fails with an explicit reason
- **AND** no downstream stage is launched

### Requirement: Validate the generated specification

The stage SHALL validate the generated change with `openspec validate
<change> --strict` before reporting success.

#### Scenario: Strict validation passes

- **WHEN** all required planning artefacts exist and strict validation exits
  successfully
- **THEN** the stage reports `passed`
- **AND** records the validation command and exit code

#### Scenario: Strict validation fails

- **WHEN** strict validation exits non-zero or a required artefact is missing
- **THEN** the stage reports `failed`
- **AND** persists the validation output for inspection

### Requirement: Persist handoff artefacts

The stage SHALL persist its prompt, Codex output, OpenSpec change name,
validation evidence and a machine-readable result under the run's stage
directory.

#### Scenario: Implementer can consume the handoff

- **WHEN** the stage passes
- **THEN** its result references the change directory, proposal, specs, design
  and tasks files
- **AND** a later stage can locate those paths from disk without conversation
  memory
