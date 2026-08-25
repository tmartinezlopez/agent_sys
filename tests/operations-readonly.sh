#!/usr/bin/env bash
set -euo pipefail

root="$(cd "$(dirname "$0")/.." && pwd)"
tmp="$(mktemp -d /tmp/reference-codex-ops-XXXXXX)"
worktree="$tmp/worktrees/feature-one"
runs="$worktree/.pipeline/runs"
mkdir -p "$runs"

python3 "$root/scripts/pipeline/run-ledger.py" init run_ops_one \
  --worktree "$worktree" >/dev/null
python3 "$root/scripts/pipeline/run-ledger.py" init run_ops_two \
  --worktree "$worktree" >/dev/null
python3 "$root/scripts/pipeline/run-ledger.py" event run_ops_one dispatched \
  --emitter test --worktree "$worktree" \
  --payload '{"taskId":"spec-writer-1","role":"spec-writer"}' >/dev/null
mkdir -p "$runs/run_ops_one/stages/spec-writer"
printf 'prompt\\n' > "$runs/run_ops_one/stages/spec-writer/prompt.md"
printf 'stdout\\n' > "$runs/run_ops_one/stages/spec-writer/stdout.log"
printf 'stderr\\n' > "$runs/run_ops_one/stages/spec-writer/stderr.log"

snapshot() {
  find "$runs" -type f -print0 | sort -z | xargs -0 sha256sum
}

before="$(snapshot)"
PIPELINE_WORKTREES_DIR="$tmp/worktrees" \
  "$root/scripts/pipeline/pipelines-status.sh" > "$tmp/status.txt"
PIPELINE_RUNS_DIR="$runs" \
  python3 "$root/scripts/pipeline/run-health-check.py" > "$tmp/health.json"
python3 "$root/scripts/pipeline/run-logs.py" run_ops_one \
  --worktree "$worktree" > "$tmp/logs.json"
python3 "$root/scripts/pipeline/run-report.py" run_ops_one \
  --worktree "$worktree" > "$tmp/report.json"
after="$(snapshot)"

[ "$before" = "$after" ] || { echo "una consulta mutó el ledger" >&2; diff -u <(printf '%s\n' "$before") <(printf '%s\n' "$after") >&2; exit 1; }
grep -q 'run_ops_one' "$tmp/status.txt"
grep -q 'run_ops_two' "$tmp/status.txt"
python3 - "$tmp/health.json" "$tmp/logs.json" "$tmp/report.json" <<'PY'
import json
import sys

health, logs, report = [json.load(open(path, encoding="utf-8")) for path in sys.argv[1:]]
assert {run["runId"] for run in health["runs"]} == {"run_ops_one", "run_ops_two"}
assert any(entry["file"] == "stdout.log" for entry in logs["logs"])
assert report["stages"][0]["role"] == "spec-writer"
PY

for command in \
  "python3 $root/scripts/pipeline/run-health-check.py run_missing --worktree $worktree" \
  "python3 $root/scripts/pipeline/run-logs.py run_missing --worktree $worktree" \
  "python3 $root/scripts/pipeline/run-report.py run_missing --worktree $worktree"; do
  if eval "$command" >/dev/null 2>&1; then
    echo "run inexistente aceptado: $command" >&2
    exit 1
  fi
done

echo "operations read-only: PASS"
