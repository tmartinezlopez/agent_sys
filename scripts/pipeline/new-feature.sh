#!/usr/bin/env bash
# Crea un worktree y una rama de feature. Con un objetivo, lanza el vertical
# slice Codex dentro del worktree; sin objetivo sólo prepara aislamiento.
set -euo pipefail

usage() {
  echo "uso: new-feature.sh <nombre-kebab-case> [objetivo] [--no-tmux] [--codex-command comando] [--timeout segundos]" >&2
  exit 1
}

item="${1:-}"
[ -n "$item" ] || usage
shift
objective=""
no_tmux=0
codex_command="codex"
timeout=""
while [ $# -gt 0 ]; do
  case "$1" in
    --no-tmux) no_tmux=1; shift ;;
    --codex-command) codex_command="${2:?--codex-command requiere comando}"; shift 2 ;;
    --timeout) timeout="${2:?--timeout requiere segundos}"; shift 2 ;;
    *) [ -z "$objective" ] || { echo "sólo se admite un objetivo" >&2; exit 1; }; objective="$1"; shift ;;
  esac
done
if ! [[ "$item" =~ ^[a-z0-9][a-z0-9-]*$ ]]; then
  echo "nombre inválido: usa kebab-case (minúsculas, dígitos y guiones)" >&2
  exit 1
fi

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib-paths.sh
source "$script_dir/lib-paths.sh"

worktree_path="$(pl_worktree_path "$item")"
branch="$(pl_branch "$item")"
if [ -e "$worktree_path" ]; then
  echo "ya existe el worktree: $worktree_path" >&2
  exit 1
fi

mkdir -p "$worktrees_dir"
git -C "$repo_root" worktree add "$worktree_path" -b "$branch"

printf 'worktree=%s\nbranch=%s\nwindow=%s\n' \
  "$worktree_path" "$branch" "$(pl_window "$item")"

if [ -z "$objective" ]; then
  exit 0
fi

pipeline="$worktree_path/scripts/pipeline/run-pipeline.sh"
command=("$pipeline" "$item" "$objective" --worktree "$worktree_path"
         --codex-command "$codex_command")
[ -n "$timeout" ] && command+=(--timeout "$timeout")

if [ "$no_tmux" -eq 0 ] && command -v tmux >/dev/null 2>&1; then
  session="$repo_name"
  if ! tmux has-session -t "=$session" 2>/dev/null; then
    tmux new-session -d -s "$session" -n despacho -c "$repo_root"
  fi
  command_line="$(printf '%q ' "${command[@]}")"
  window_id="$(tmux new-window -P -F '#{window_id}' -t "=$session" -c "$worktree_path" \
    -n "$(pl_window "$item")" "set +e; $command_line; rc=\$?; echo PIPELINE_EXIT=\$rc; exec bash")"
  pl_record_window_id "$item" "$window_id"
  echo "pipeline=$item window=$window_id session=$session"
  exit 0
fi

echo "tmux no disponible o desactivado; ejecutando foreground"
"${command[@]}"
