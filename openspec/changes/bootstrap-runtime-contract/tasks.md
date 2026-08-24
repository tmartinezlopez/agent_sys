## 1. Bootstrap and project context

- [x] 1.1 Resolve the project Git root without overwriting the existing directory, and verify the chosen root with `git rev-parse --show-toplevel`
- [x] 1.2 Fill `openspec/config.yaml` with the real Python/Bash stack, local constraints and quality commands, and verify it with `openspec doctor`

## 2. Canonical pipeline contract

- [x] 2.1 Add the six-role catalog with the agreed model, reasoning, sandbox, timeout, retry and prompt-contract fields, and verify every role is present with a focused configuration test
- [x] 2.2 Add canonical stage ordering and valid transition rules, and verify invalid predecessor/gate transitions are rejected by focused tests
- [x] 2.3 Define the JSON shape for run state, stage results and events, and verify representative documents parse and preserve required fields

## 3. Persistent run state

- [x] 3.1 Implement run creation, current-state projection and append-only event recording, and verify a run can be reconstructed from its files after a fresh process
- [x] 3.2 Persist stage prompts, stdout, stderr, exit codes, errors and artefact references, and verify passed, failed and blocked outcomes with focused tests

## 4. Owned tmux runtime

- [x] 4.1 Implement project-session discovery/creation and named stage-window creation without numeric targets, and verify the commands against an isolated tmux server
- [x] 4.2 Add ownership checks and safe stop/observation behavior, and verify unrelated sessions and windows are not renamed or killed

## 5. External Codex stage launcher

- [x] 5.1 Build the role-specific `codex exec` argument vector from the canonical configuration and record it before launch, and verify model, reasoning, sandbox and working-directory metadata
- [x] 5.2 Launch the process in an owned process group with timeout handling and persisted logs, and verify success, non-zero exit, missing binary and timeout outcomes

## 6. Coordinator vertical slice

- [x] 6.1 Connect one configured stage to the tmux runtime, launcher and ledger, and verify an observable passed run from the coordinator entry point
- [x] 6.2 Verify that a failed or blocked stage prevents its successor from launching and records the stopping reason

## 7. Handoff to role implementation

- [x] 7.1 Document the next change as the real `spec-writer` stage using OpenSpec, with no generic-agent fallback, and verify the runtime contract exposes the inputs and artefacts it requires
