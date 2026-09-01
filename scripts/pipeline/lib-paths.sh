#!/usr/bin/env bash
# Convenciones de rutas y nombres del runtime. Sourceable y sin efectos
# colaterales: no ejecuta Git, no cambia el directorio y no crea ficheros.

_pipeline_paths_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="${PIPELINE_REPO_ROOT:-$(cd "$_pipeline_paths_dir/../.." && pwd)}"
repo_name="$(basename "$repo_root")"
worktrees_dir="${PIPELINE_WORKTREES_DIR:-$(dirname "$repo_root")/${repo_name}-features}"
unset _pipeline_paths_dir

pl_worktree_path() { # <item>
  printf '%s\n' "$worktrees_dir/$1"
}

pl_branch() { # <item>
  printf 'feature/%s\n' "$1"
}

pl_window() { # <item>
  printf 'pl:%s\n' "$1"
}

pl_window_id_file() { # <item>
  printf '%s\n' "$(pl_worktree_path "$1")/.pipeline/window-id"
}

pl_record_window_id() { # <item> <window_id>
  local item="${1:-}" window_id="${2:-}" target
  [ -n "$item" ] && [ -n "$window_id" ] || return 0
  target="$(pl_window_id_file "$item")"
  mkdir -p "$(dirname "$target")"
  printf '%s\n' "$window_id" > "$target"
}

pl_find_run_worktree() { # <run_id>
  local run_id="${1:-}" candidate
  [ -n "$run_id" ] || return 1
  for candidate in "$repo_root" "$worktrees_dir"/*/; do
    candidate="${candidate%/}"
    [ -d "$candidate/.pipeline/runs/$run_id" ] || continue
    printf '%s\n' "$candidate"
    return 0
  done
  return 1
}
