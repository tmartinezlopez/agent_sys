## Context

The reference repository separates role contracts in `.claude/agents/` from
the runtime in `scripts/pipeline/`, uses a canonical stage order and persists
auditable run state. Our project currently has a single direct subprocess
runner, OpenSpec is initialized for Codex, and the current directory has no
Git metadata. The architecture must preserve the reference's useful
boundaries while replacing native Claude delegation with `codex exec`.

## Goals / Non-Goals

**Goals:**

- Capture the final architecture before implementation expands.
- Turn the architecture into a dependency-ordered backlog.
- Make each backlog item independently verifiable and ready to become an
  OpenSpec implementation change.

**Non-Goals:**

- Implement the runtime, tmux manager or any role.
- Choose a new model or alter the agreed role model mapping.
- Initialise Git, create worktrees or touch unrelated tmux sessions.

## Decisions

### Architecture before role execution

The six roles are part of the final design from the start, but the first code
work builds the state, transport and launch boundaries they all share. This
avoids a role-specific path becoming the permanent architecture by accident.

### Backlog as the dependency map

The backlog is the human-readable map of future changes. Each implementation
change will later be created separately with OpenSpec; this change does not
pre-create a directory for every future change.

### Runtime layers

The design uses these layers:

```text
operator
  -> coordinator
  -> persistent run state / events
  -> tmux session and named stage windows
  -> codex exec adapter
  -> role contract and artefacts
```

Recovery and operator status consume the same state and events rather than
maintaining a second source of truth.

### Worktree prerequisite

Git worktrees are required for write-capable isolation, but the current path is
not a Git checkout. The backlog records this as an explicit prerequisite; no
automatic `git init`, clone or overwrite is allowed.

## Risks / Trade-offs

- [Risk] A large architecture document becomes detached from implementation →
  Mitigation: every backlog item has a concrete deliverable and verification
  criterion, and later changes must update the relevant architecture decision.
- [Risk] The reference's native-subagent behavior is assumed to map directly to
  external Codex → Mitigation: document process boundaries, prompts, files and
  exit codes explicitly.
- [Risk] Git setup delays work → Mitigation: state/contract design can proceed,
  while worktree-dependent implementation remains blocked and visible.
