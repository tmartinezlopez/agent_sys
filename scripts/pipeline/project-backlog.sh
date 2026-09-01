#!/usr/bin/env bash
# Localiza el backlog del proyecto, excluyendo el backlog interno de la metodología.
set -euo pipefail
worktree="${PIPELINE_REPO_ROOT:-$(pwd)}"
while [ $# -gt 0 ]; do
  case "$1" in
    --worktree) worktree="${2:?--worktree requiere ruta}"; shift 2 ;;
    -h|--help) echo "uso: project-backlog.sh [--worktree ruta]"; exit 0 ;;
    *) echo "argumento desconocido: $1" >&2; exit 1 ;;
  esac
done
worktree="$(cd "$worktree" && pwd)"
features_dir="${PIPELINE_WORKTREES_DIR:-$(dirname "$worktree")/$(basename "$worktree")-features}"
roots=("$worktree")
if [ -d "$features_dir" ]; then
  while IFS= read -r root; do roots+=("$root"); done < <(find "$features_dir" -mindepth 1 -maxdepth 1 -type d -print | sort)
fi
found=0
for root in "${roots[@]}"; do
  for candidate in "$root/BACKLOG.md" "$root/backlog.md" \
    "$root/TASKS.md" "$root/tasks.md" \
    "$root/docs/BACKLOG.md" "$root/docs/backlog.md" \
    "$root/.project/BACKLOG.md" "$root/.project/backlog.md"; do
    if [ -f "$candidate" ]; then printf '%s\n' "$candidate"; found=1; fi
  done
  while IFS= read -r candidate; do
    printf '%s\n' "$candidate"
    found=1
  done < <(find "$root/docs" -maxdepth 1 -type f \
    \( -iname '*backlog*.md' -o -iname '*tasks*.md' \) \
    -not -path '*/metodologia/*' -print 2>/dev/null | sort)
done
if [ "$found" -eq 0 ]; then
  echo "NO_PROJECT_BACKLOG worktree=$worktree" >&2
  exit 1
fi
