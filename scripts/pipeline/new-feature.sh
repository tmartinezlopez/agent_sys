#!/usr/bin/env bash
# Crea un worktree y una rama de feature. El despacho Codex se añadirá en el
# vertical slice posterior; este primer paso sólo prepara aislamiento.
set -euo pipefail

usage() {
  echo "uso: new-feature.sh <nombre-kebab-case>" >&2
  exit 1
}

item="${1:-}"
[ -n "$item" ] || usage
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
