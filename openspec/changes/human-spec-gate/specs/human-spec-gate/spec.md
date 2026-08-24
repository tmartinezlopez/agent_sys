## ADDED Requirements

### Requirement: The pipeline pauses at the spec review gate
After `spec-writer` passes, the coordinator MUST persist a `spec-review` gate
with status `pending` and MUST NOT launch `implementer` automatically.

#### Scenario: Specification succeeds
- **WHEN** `spec-writer` passes and no gate decision was supplied
- **THEN** the run MUST finish in a resumable blocked state
- **AND** `run.json` and `events.jsonl` MUST identify the pending gate

#### Scenario: Specification fails
- **WHEN** `spec-writer` fails or is blocked
- **THEN** no gate is created as approvable
- **AND** `implementer` MUST NOT launch

### Requirement: The operator makes an explicit persisted decision
The coordinator MUST accept only `approve` or `reject` for `spec-review` and
MUST persist the decision, operator identity, optional reason and timestamp.

#### Scenario: Operator approves
- **WHEN** the operator approves a pending gate for an existing run
- **THEN** the gate becomes `approved`
- **AND** an event records the decision before resumption

#### Scenario: Operator rejects
- **WHEN** the operator rejects a pending gate
- **THEN** the gate becomes `rejected`
- **AND** implementer and all later stages become `blocked`

### Requirement: Approved runs resume without duplicating completed stages
The coordinator MUST resume an approved run from `implementer`, preserving the
existing `run_id`, artifacts and completed `spec-writer` stage.

#### Scenario: Approved run resumes
- **WHEN** the gate is approved and the run is resumed
- **THEN** `spec-writer` MUST NOT execute again
- **AND** the pipeline MUST continue through the declared remaining stages

#### Scenario: Gate is missing, already decided, or run is unknown
- **WHEN** approval targets an unknown run, a missing gate, or a decided gate
- **THEN** the command MUST fail without changing the ledger.

### Requirement: Gate operation is observable
The gate decision and every resume attempt MUST be represented in the run
ledger and event log, including the command result and reason for refusal.

#### Scenario: Decision is recorded
- **WHEN** the operator approves, rejects, or attempts an invalid gate operation
- **THEN** the event log MUST contain the operation outcome and its reason
