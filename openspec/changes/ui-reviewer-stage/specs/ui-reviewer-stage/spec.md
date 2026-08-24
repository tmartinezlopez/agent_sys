## Purpose

Define the conditional visual review stage that uses a real browser when UI is
affected and explicitly reports when visual verification is unavailable.

## ADDED Requirements

### Requirement: Run only for UI changes

The `ui-reviewer` SHALL run only when the change affects frontend pages or
components and SHALL be skipped with an explicit reason otherwise.

#### Scenario: Change does not affect UI

- **WHEN** the diff and change artefacts contain no frontend scope
- **THEN** the stage is recorded as `skipped`
- **AND** no browser process is launched

#### Scenario: Change affects UI

- **WHEN** frontend files or UI scenarios are present
- **THEN** the stage requires browser verification before deciding its result

### Requirement: Require real browser capability

The stage SHALL use a configured real browser bridge and a reachable
development server; it SHALL never report `passed` from text-only or simulated
evidence.

#### Scenario: Browser and server are available

- **WHEN** a real browser bridge is configured and the application responds
- **THEN** the stage checks the UI scenarios and persists visual evidence

#### Scenario: Browser capability is unavailable

- **WHEN** no browser bridge or development server is available
- **THEN** the stage reports `NO_VERIFICABLE` and records the blocking reason
- **AND** it does not claim that the UI passed

### Requirement: Preserve read-only behavior

The stage SHALL not modify source, tests, configuration, browser user data or
Git history, and SHALL close only browser tabs it created.

#### Scenario: Visual review completes safely

- **WHEN** the stage finishes
- **THEN** checkout status and unrelated browser tabs are unchanged
- **AND** the result references each scenario's evidence or non-verifiability
