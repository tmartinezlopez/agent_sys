## ADDED Requirements

### Requirement: QA validates the complete pipeline handoff
The `qa` stage MUST receive the original objective and the persisted handoffs
from `spec-writer`, `implementer`, `test-runner`, `reviewer`, and, when
applicable, `ui-reviewer`.

#### Scenario: Complete evidence is available
- **WHEN** all required predecessor stages are `passed`, or `ui-reviewer` is
  explicitly `skipped` because the change does not affect UI
- **THEN** `qa` MAY launch Codex in read-only mode with the objective and
  machine-readable paths to the predecessor artifacts
- **AND** the prompt MUST require an explicit structured decision

#### Scenario: A required predecessor is not passed
- **WHEN** a predecessor is `pending`, `running`, `failed`, or `blocked`
- **THEN** the coordinator MUST NOT launch `qa`
- **AND** `qa` MUST be recorded as `blocked` with the blocking predecessor

### Requirement: QA produces a structured final decision
The `qa` agent MUST emit exactly one decision marker in its final output:
`AGENT_SYS_QA: passed` or `AGENT_SYS_QA: blocked`.

It MUST emit zero or more findings using:
`AGENT_SYS_QA_FINDING: <severity>|<evidence>|<explanation>`.

#### Scenario: QA approves delivery
- **WHEN** the agent emits `AGENT_SYS_QA: passed` and the process exits with
  code zero
- **THEN** the coordinator MUST transition the stage to `passed`
- **AND** persist the decision and findings in `qa-summary.json` and `result.json`

#### Scenario: QA blocks delivery
- **WHEN** the agent emits `AGENT_SYS_QA: blocked`, exits non-zero, or omits a
  valid decision marker
- **THEN** the coordinator MUST transition the stage to `blocked` or `failed`
  according to whether the failure is a QA decision or an execution failure
- **AND** persist the raw output and the reason.

### Requirement: QA is read-only
The coordinator MUST launch `qa` with the configured `read-only` sandbox and
MUST verify that the checkout status before and after execution is unchanged.

#### Scenario: QA attempts to modify the checkout
- **WHEN** tracked or untracked files change during QA
- **THEN** the coordinator MUST record the mutation as a QA failure
- **AND** MUST NOT report the stage as passed.

### Requirement: QA is observable and resumable
The coordinator MUST persist the exact prompt/command metadata, process exit
code, stdout/stderr paths, decision, findings, and timestamps in the run
directory and ledger.

#### Scenario: QA process times out or cannot start
- **WHEN** Codex cannot start or exceeds the configured timeout
- **THEN** the coordinator MUST persist the error and transition the stage to
  `failed` or `blocked` as appropriate
- **AND** MUST NOT launch any later stage.

