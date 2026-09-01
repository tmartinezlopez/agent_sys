#!/usr/bin/env bash
# Implementación común de los launchers de roles.
set -euo pipefail

role="${1:-}"
run_id="${2:-}"
[ -n "$role" ] && [ -n "$run_id" ] || {
  echo "uso: launch-role.sh <rol> <run_id> --worktree ruta [--change nombre] [--codex-command comando] [--timeout segundos]" >&2
  exit 1
}
shift 2
tmux_mode=0
tmux_session="${PIPELINE_TMUX_SESSION:-}"
forward=()
while [ $# -gt 0 ]; do
  case "$1" in
    --tmux) tmux_mode=1; shift ;;
    --tmux-session) tmux_session="${2:?--tmux-session requiere nombre}"; shift 2 ;;
    *) forward+=("$1"); shift ;;
  esac
done
case "$role" in
  spec-writer|implementer|test-runner|reviewer|ui-reviewer|qa) ;;
  *) echo "rol no permitido: $role" >&2; exit 1 ;;
esac
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
engine="${PIPELINE_STAGE_ENGINE:-$script_dir/run-stage.sh}"
if [ "$tmux_mode" -eq 0 ]; then
  exec "$engine" "$run_id" "$role" "${forward[@]}"
fi

command -v tmux >/dev/null 2>&1 || {
  echo "tmux requerido para lanzar $role en una ventana visible" >&2
  exit 1
}
worktree="${PIPELINE_REPO_ROOT:-$(pwd)}"
for ((i=0; i<${#forward[@]}; i++)); do
  if [ "${forward[$i]}" = --worktree ] && [ $((i + 1)) -lt ${#forward[@]} ]; then
    worktree="${forward[$((i + 1))]}"
  fi
done
worktree="$(cd "$worktree" && pwd)"
tmux_session="${tmux_session:-$(basename "$worktree")-coordinator}"
if ! tmux has-session -t "$tmux_session" 2>/dev/null; then
  tmux new-session -d -s "$tmux_session" -n coordinator -c "$worktree"
fi
window="role-$role"
tmux kill-window -t "$tmux_session:$window" 2>/dev/null || true
env_args=("PIPELINE_SCRIPT_DIR=$script_dir" "PIPELINE_REPO_ROOT=$worktree"
  "PIPELINE_STAGE_ENGINE=$engine")
[ "${PIPELINE_PRESERVE_PROMPT:-}" = 1 ] && env_args+=(PIPELINE_PRESERVE_PROMPT=1)
env_args+=(PIPELINE_LIVE_OUTPUT=1)
tmux new-window -d -t "$tmux_session" -n "$window" -c "$worktree" \
  env "${env_args[@]}" \
  "$engine" "$run_id" "$role" "${forward[@]}"
tmux set-window-option -t "$tmux_session:$window" remain-on-exit off
tmux set-window-option -t "$tmux_session:$window" automatic-rename off
tmux select-pane -t "$tmux_session:$window" -T "ROLE:$role"
tmux rename-window -t "$tmux_session:$window" "ROLE:$role"
tmux select-window -t "$tmux_session:$window"
echo "ROLE_WINDOW session=$tmux_session window=$window role=$role run_id=$run_id"
