#!/usr/bin/env bash
# Arranca una sesión tmux nueva para un coordinador sin reutilizar contexto previo.
set -euo pipefail

worktree="${PIPELINE_REPO_ROOT:-$(pwd)}"
codex_command="codex"
detach=0
open_terminal=1
while [ $# -gt 0 ]; do
  case "$1" in
    --worktree) worktree="${2:?--worktree requiere ruta}"; shift 2 ;;
    --codex-command) codex_command="${2:?--codex-command requiere comando}"; shift 2 ;;
    --detach) detach=1; shift ;;
    --no-open-terminal) open_terminal=0; shift ;;
    -h|--help) echo "uso: coordinator-start.sh --worktree ruta [--codex-command comando] [--detach]"; exit 0 ;;
    *) echo "argumento desconocido: $1" >&2; exit 1 ;;
  esac
done
worktree="$(cd "$worktree" && pwd)"
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
command -v tmux >/dev/null 2>&1 || { echo "FALTA tmux" >&2; exit 1; }

export PIPELINE_REPO_ROOT="$worktree"
export PIPELINE_SCRIPT_DIR="$script_dir"
preflight_args=("$script_dir/preflight.sh" --worktree "$worktree")
[ "$(basename "$codex_command")" = codex ] && preflight_args+=(--real)
"${preflight_args[@]}" >/dev/null

project="$(basename "$worktree" | tr '[:upper:] ' '[:lower:]_')"
session="${project}-coordinator-$(date -u +%Y%m%d-%H%M%S)-$$"
mkdir -p "$worktree/.pipeline/coordinators"
state="$worktree/.pipeline/coordinators/$session.state"
printf 'session=%s\nworktree=%s\nstatus=starting\ncreated_at=%s\n' \
  "$session" "$worktree" "$(date -u +%Y-%m-%dT%H:%M:%SZ)" > "$state"
env_args=("PIPELINE_REPO_ROOT=$worktree" "PIPELINE_SCRIPT_DIR=$script_dir"
  "PIPELINE_TMUX_SESSION=$session")
tmux new-session -d -s "$session" -n coordinator -c "$worktree" \
  env "${env_args[@]}" "$script_dir/coordinator.sh" \
  --worktree "$worktree" --codex-command "$codex_command"
tmux set-window-option -t "$session:coordinator" automatic-rename off
tmux set-window-option -t "$session:coordinator" remain-on-exit on
tmux select-pane -t "$session:coordinator" -T "COORDINATOR"
tmux rename-window -t "$session:coordinator" "COORDINATOR"
tmux set-option -t "$session" history-limit 10000
tmux set-option -t "$session" mouse on
tmux set-window-option -t "$session" mode-keys emacs
"$script_dir/tmux-setup.sh" --session "$session" >/dev/null
sed -i 's/^status=.*/status=running/' "$state"
printf 'COORDINATOR_SESSION=%s\n' "$session"
printf 'ATTACH: tmux attach-session -t %q\n' "$session"
if [ "$detach" -eq 0 ] && [ "$open_terminal" -eq 1 ] && [ -n "${DISPLAY:-}${WAYLAND_DISPLAY:-}" ]; then
  if command -v gnome-terminal >/dev/null 2>&1; then
    gnome-terminal --title="COORDINATOR $project" -- bash -lc \
      "exec tmux attach-session -t '$session'" >/dev/null 2>&1 &
  elif command -v x-terminal-emulator >/dev/null 2>&1; then
    x-terminal-emulator -T "COORDINATOR $project" -e \
      bash -lc "exec tmux attach-session -t '$session'" >/dev/null 2>&1 &
  fi
fi
if [ "$detach" -eq 0 ] && [ "$open_terminal" -eq 0 ] && [ -t 1 ]; then
  exec tmux attach-session -t "$session"
fi
