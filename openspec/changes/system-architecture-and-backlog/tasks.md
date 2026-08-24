## 1. Architecture documentation

- [x] 1.1 Write `docs/ARCHITECTURE.md` with the operator, coordinator, tmux, pipeline, Codex process, state and artefact boundaries, and verify every boundary is represented in the document
- [x] 1.2 Document the six real roles, their agreed model/reasoning/sandbox mapping and the canonical stage order, and verify it matches the role catalog defined by the project

## 2. Dependency-ordered backlog

- [x] 2.1 Write `docs/BACKLOG.md` with ordered items for bootstrap, run state, ledger, stage transitions, tmux, Codex launcher, spec-writer, gates, remaining roles, watchdog, resume and operator observability, and verify every item has prerequisites and completion evidence
- [x] 2.2 Record the current Git-root limitation, OpenSpec installation, Codex authentication and tmux availability in the backlog, and verify the status is based on commands executed in this repository

## 3. Contract alignment

- [x] 3.1 Align `CONTRATO_PIPELINE.md` with the architecture and backlog, removing any description that implies the direct single-agent runner is the final system, and verify the document describes the same artefact and state vocabulary
- [x] 3.2 Validate the OpenSpec change and inspect the final architecture/backlog documents together, and verify no implementation task is started before its listed prerequisite
