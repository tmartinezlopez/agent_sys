#!/usr/bin/env bash
# Cierra únicamente la sesión tmux indicada del coordinador.
set -euo pipefail

session=""
worktree="${PIPELINE_REPO_ROOT:-$(pwd)}"
while [ $# -gt 0 ]; do
  case "$1" in
    --session) session="${2:?--session requiere nombre}"; shift 2 ;;
    --worktree) worktree="${2:?--worktree requiere ruta}"; shift 2 ;;
    -h|--help) echo "uso: coordinator-stop.sh --session nombre"; exit 0 ;;
    *) echo "argumento desconocido: $1" >&2; exit 1 ;;
  esac
done
[ -n "$session" ] || { echo "debes indicar --session explícitamente" >&2; exit 1; }
worktree="$(cd "$worktree" && pwd)"
case "$session" in
  *coordinator-*) ;;
  *) echo "sesión no reconocida como coordinador: $session" >&2; exit 1 ;;
esac
if tmux has-session -t "$session" 2>/dev/null; then
  tmux kill-session -t "$session"
  for state in "$worktree/.pipeline/coordinators/$session.state"; do
    [ -f "$state" ] || continue
    sed -i 's/^status=.*/status=stopped/' "$state"
    printf 'stopped_at=%s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" >> "$state"
  done
  printf 'COORDINATOR_STOPPED session=%s\n' "$session"
else
  printf 'COORDINATOR_NOT_RUNNING session=%s\n' "$session"
fi
