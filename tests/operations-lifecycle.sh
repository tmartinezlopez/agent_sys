#!/usr/bin/env bash
set -euo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
tmp="$(mktemp -d /tmp/reference-codex-lifecycle-XXXXXX)"
trap 'rm -rf "$tmp"' EXIT

python3 "$root/scripts/pipeline/run-ledger.py" init run_gate --worktree "$tmp" >/dev/null
python3 "$root/scripts/pipeline/run-ledger.py" event run_gate dispatched --emitter test \
  --worktree "$tmp" --payload '{"taskId":"spec-writer-1","role":"spec-writer"}' >/dev/null
python3 "$root/scripts/pipeline/run-ledger.py" event run_gate completed --emitter test \
  --worktree "$tmp" --payload '{"taskId":"spec-writer-1","role":"spec-writer"}' >/dev/null
python3 "$root/scripts/pipeline/run-ledger.py" event run_gate gate_opened --emitter test \
  --worktree "$tmp" --payload '{"gateId":"gate_spec","taskId":"spec-writer-1"}' >/dev/null
"$root/scripts/pipeline/gate.sh" run_gate changes operator "ajustar spec" --worktree "$tmp" >/dev/null
"$root/scripts/pipeline/gate.sh" run_gate approve operator --worktree "$tmp" >/dev/null

python3 "$root/scripts/pipeline/run-ledger.py" event run_gate gate_opened --emitter test \
  --worktree "$tmp" --payload '{"gateId":"gate_release","taskId":"qa-1"}' >/dev/null
"$root/scripts/pipeline/gate.sh" run_gate discard operator "descartado" \
  --gate gate_release --worktree "$tmp" >/dev/null
python3 - "$tmp" <<'PY'
import json
from pathlib import Path
import sys
state = json.loads((Path(sys.argv[1]) / ".pipeline/runs/run_gate/current-state.json").read_text())
assert state["status"] == "discarded", state
PY

python3 "$root/scripts/pipeline/run-ledger.py" init run_old --worktree "$tmp" >/dev/null
python3 "$root/scripts/pipeline/run-ledger.py" summary run_old --worktree "$tmp" >/dev/null
touch -d '2 days ago' "$tmp/.pipeline/runs/run_old/summary.json"
listed="$("$root/scripts/pipeline/clean-runs.sh" --worktree "$tmp" --older-than 3600)"
printf '%s\n' "$listed" | grep -q 'run_old'
"$root/scripts/pipeline/clean-runs.sh" --worktree "$tmp" --older-than 3600 --force >/dev/null
[ ! -d "$tmp/.pipeline/runs/run_old" ]

echo "operations lifecycle: PASS"
