## Purpose

Define the read-only reviewer stage that evaluates implementation quality and
test evidence before the pipeline can proceed to later delivery checks.

## ADDED Requirements

### Requirement: Consume implementation and test evidence

The reviewer SHALL run only after implementer and test-runner pass and SHALL
receive their persisted result paths and checkout context.

#### Scenario: Review context is complete

- **WHEN** both previous stages are passed and their artefacts exist
- **THEN** reviewer starts in read-only mode with explicit paths

#### Scenario: Review context is incomplete

- **WHEN** a previous stage is not passed or evidence is missing
- **THEN** reviewer is blocked and no Codex review process starts

### Requirement: Produce structured findings

The reviewer SHALL inspect the implementation and report findings with
severity, evidence path, explanation and a decision to pass or block.

#### Scenario: Review passes

- **WHEN** no blocking finding exists and evidence is sufficient
- **THEN** reviewer reports `passed` with a persisted review summary

#### Scenario: Review blocks delivery

- **WHEN** a critical finding or missing evidence is detected
- **THEN** reviewer reports `failed` or `blocked`
- **AND** later delivery stages are not launched

### Requirement: Preserve read-only behavior

The reviewer SHALL not modify source, tests, configuration or Git history.

#### Scenario: Review completes without mutation

- **WHEN** reviewer finishes
- **THEN** the checkout status is unchanged and the review evidence is stored
  under the run directory
