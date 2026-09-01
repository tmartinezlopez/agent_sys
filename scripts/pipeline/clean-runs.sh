#!/usr/bin/env bash
# Lista o elimina runs terminados y antiguos. Por defecto sólo lista.
set -euo pipefail

worktree="$(pwd)"
older_than=""
force=0
while [ $# -gt 0 ]; do
  case "$1" in
    --worktree) worktree="$2"; shift 2 ;;
    --older-than) older_than="$2"; shift 2 ;;
    --force) force=1; shift ;;
    *) echo "uso: clean-runs.sh --older-than segundos [--worktree ruta] [--force]" >&2; exit 1 ;;
  esac
done
[ -n "$older_than" ] || { echo "--older-than es obligatorio" >&2; exit 1; }
worktree="$(cd "$worktree" && pwd)"
runs="$worktree/.pipeline/runs"
[ -d "$runs" ] || { echo "sin runs: $runs"; exit 0; }
cutoff="$(python3 - "$older_than" <<'PY'
import sys
import time
try:
    seconds = float(sys.argv[1])
except ValueError as exc:
    raise SystemExit("--older-than debe ser numérico") from exc
if seconds < 0:
    raise SystemExit("--older-than debe ser >= 0")
print(time.time() - seconds)
PY
)"
cutoff_int="$(printf '%.0f' "$cutoff")"
for run_dir in "$runs"/*; do
  [ -d "$run_dir" ] || continue
  [ -f "$run_dir/summary.json" ] || continue
  mtime="$(stat -c %Y "$run_dir/summary.json")"
  [ "$mtime" -lt "$cutoff_int" ] || continue
  printf '%s\n' "$run_dir"
  if [ "$force" -eq 1 ]; then
    rm -rf -- "$run_dir"
  fi
done
