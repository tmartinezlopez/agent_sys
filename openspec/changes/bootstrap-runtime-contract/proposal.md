## Why

`agent_sys` currently launches one external Codex process directly from Python,
but the target system is a multi-stage pipeline with six real roles, tmux
visibility, persistent state, gates and recovery. We need a small runtime
contract before implementing any role so that each role is built against the
same execution model and does not become a disconnected prototype.

## What Changes

- Define the canonical six pipeline roles and their order: `spec-writer`,
  `implementer`, `test-runner`, `reviewer`, `ui-reviewer` and `qa`.
- Define role configuration, stage states, transitions, events, artefacts,
  timeouts and exit-code semantics.
- Define the project tmux session/window contract using named targets and
  ownership checks, without touching unrelated sessions.
- Define the boundary between the operator, coordinator, tmux runtime and
  external `codex exec` processes.
- Record the implementation backlog and its dependencies so role work follows
  the runtime foundation.
- Keep Git worktrees out of the implementation until this directory has a
  valid Git root; the current checkout check returns “not a git repository”.

## Capabilities

### New Capabilities

- `pipeline-runtime`: Contract for role configuration, stage execution,
  persistent run state, events, tmux ownership and advancement conditions.

### Modified Capabilities

<!-- No existing OpenSpec capabilities exist yet. -->

## Impact

- Extends the current Python coordinator and its Bash entry point.
- Adds runtime configuration and OpenSpec contract files; no external API is
  introduced.
- Establishes the integration boundary used later by all six Codex roles.
- Requires the installed OpenSpec CLI and the locally authenticated Codex CLI
  at execution time, but does not use the OpenAI API.
