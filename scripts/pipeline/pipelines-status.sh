#!/usr/bin/env bash
# Vista global read-only del estado de runs del repo y sus worktrees.
set -euo pipefail

script_dir="$(cd "$(dirname "$0")" && pwd)"
# shellcheck source=lib-paths.sh
source "$script_dir/lib-paths.sh"

found=0
for dir in "$repo_root" "$worktrees_dir"/*; do
  [ -d "$dir/.pipeline/runs" ] || continue
  found=1
  printf '== %s ==\n' "$(basename "$dir")"
  report="$(PIPELINE_RUNS_DIR="$dir/.pipeline/runs" \
    python3 "$script_dir/run-health-check.py")"
  python3 -c '
import json, sys
data = json.load(sys.stdin)
for run in data["runs"]:
    run_id = run["runId"]
    status = run["status"]
    events = run["eventCount"]
    gate = " · GATE PENDIENTE" if run["pendingGates"] else ""
    print(f"  {run_id}: {status} · {events} eventos{gate}")
for finding in data["findings"]:
    kind = finding["kind"]
    run_id = finding["runId"]
    print(f"  ⚠ {kind}: {run_id}")
' <<<"$report"
done

[ "$found" = 1 ] || printf 'sin runs de pipeline (ni en el repo ni en %s)\n' "$worktrees_dir"
