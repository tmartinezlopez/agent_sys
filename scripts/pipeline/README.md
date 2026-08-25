# Runtime del pipeline

Esta carpeta contiene la mecánica operativa del sistema: worktrees, ledger,
despacho Codex, gates, reanudación, consultas y parada segura. Los contratos de
los roles se mantienen separados de esta capa.

## Flujo principal

- new-feature.sh <item> <objetivo> crea feature/<item> en un worktree y
  lanza el slice spec-writer.
- gate.sh <run_id> approve|changes|discard --worktree <ruta> registra la
  decisión humana.
- resume-run.sh <run_id> --worktree <ruta> continúa el mismo run en
  implementer después de aprobar el gate.
- stop-run.sh <run_id> --worktree <ruta> --force detiene sólo la ventana tmux
  registrada para ese run y deja el worktree intacto.

Cada run queda en .pipeline/runs/<run_id>/ con run.json, events.jsonl,
estado derivado y evidencias por etapa. Ese estado es local y está ignorado
por Git.

## Consultas

- pipelines-status.sh lista los runs del checkout y sus worktrees.
- run-health-check.py devuelve triage JSON read-only, incluidos gates y
  posibles estancamientos.
- run-logs.py <run_id> muestra eventos, prompts y stdout/stderr persistidos.
- run-report.py <run_id> resume etapas, modelos, sandbox y resultados Codex.

Las consultas leen el ledger en memoria: no regeneran current-state.json, no
añaden eventos y no crean summary.json.

## Seguridad

codex-run.py ejecuta sólo roles declarados en roles.json y antepone
git-guard.sh al PATH del proceso agente. El wrapper rechaza git merge y
git push; la integración de la rama queda para una revisión humana posterior.

Las funciones de lib-paths.sh son la única fuente de verdad para nombres de
worktrees, ramas, ventanas y runs. Los scripts no hacen merge ni push por sí
mismos.
