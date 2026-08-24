## Context

The current implementation in `src/agent_sys/pipeline.py` launches one
external process directly and persists a run-local JSON result. The target
system must adapt the separation used by `rburgosm/agentic-system`: role
contracts are distinct from runtime scripts, while external Codex processes
replace Claude's native subagents. The local directory currently has no Git
root, so worktree operations are a prerequisite rather than an assumption.

## Goals / Non-Goals

**Goals:**

- Establish one source of truth for six real role configurations.
- Make state and transitions reconstructable from disk.
- Run and observe stages through owned, named tmux windows.
- Preserve exact Codex launch metadata and stage artefacts.
- Make the first real role (`spec-writer`) use this runtime later.

**Non-Goals:**

- Implement the six role prompts in this change.
- Implement watchdog, resume, human gates or worktree creation beyond the
  prerequisites and interfaces they require.
- Integrate with GitHub, the OpenAI API or Claude.
- Add a second orchestration framework or a generic abstraction layer.

## Decisions

### Runtime and role contracts are separate

The runtime owns process lifecycle, tmux, state and events. Role configuration
owns model, reasoning, sandbox, prompt and required artefacts. This follows the
reference repository's separation between `scripts/pipeline/` and
`.claude/agents/`, adapted to external Codex processes.

### Six roles are declared before six roles are implemented

The catalog is canonical from the beginning, so the coordinator cannot fall
back to an untyped generic agent. Implementation proceeds vertically, starting
with `spec-writer` after the shared runtime is verified.

### Tmux uses project ownership and names

The coordinator uses a project session and named windows such as
`run:<run_id>:<role>`. It targets `session:window-name` or an ownership-derived
window id, never a numeric index. It must not stop or rename unrelated sessions.

### State is file-based and append-oriented

`run.json` is the current projection; `events.jsonl` is the append-only audit
stream; stage directories hold prompts, process logs and results. This permits
inspection and later resume without hidden memory.

### Git is an explicit prerequisite for worktrees

The current directory is not a Git checkout. This change records the
prerequisite and leaves clone/initialisation to an explicit operator decision;
the runtime must not silently run `git init` or clone over existing files.

## Risks / Trade-offs

- [Risk] tmux sessions can be restored or pre-exist with stale windows →
  Mitigation: persist ownership metadata and verify named targets before any
  mutation.
- [Risk] Codex CLI configuration names for reasoning effort can vary by
  version → Mitigation: validate the installed CLI/config key before emitting
  a role command; fail clearly rather than silently dropping `medium`.
- [Risk] A process can spawn children beyond a simple timeout → Mitigation:
  launch in an owned process group and terminate only that group.
- [Risk] Write-capable roles may need isolation → Mitigation: keep worktree
  creation out of this change until a valid Git root is established.
