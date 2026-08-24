#!/usr/bin/env bash
set -euo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
tmp="$(mktemp -d /tmp/reference-codex-contract-XXXXXX)"
trap 'rm -rf "$tmp"' EXIT

printf '#!/usr/bin/env bash\nprintf "fake codex\\n"\n' > "$tmp/fake-codex"
chmod +x "$tmp/fake-codex"
python3 "$root/scripts/pipeline/run-ledger.py" init run_contract_20260824-1200 --worktree "$tmp"
python3 "$root/scripts/pipeline/stage-guard.py" --role spec-writer \
  --run-id run_contract_20260824-1200 --worktree "$tmp" >/dev/null

if python3 "$root/scripts/pipeline/stage-guard.py" --role implementer \
  --run-id run_contract_20260824-1200 --worktree "$tmp" 2>/dev/null; then
  echo "implementer se permitió sin gate" >&2
  exit 1
fi

python3 "$root/scripts/pipeline/run-ledger.py" event run_contract_20260824-1200 dispatched \
  --emitter test --worktree "$tmp" \
  --payload '{"taskId":"spec-writer-1","role":"spec-writer"}' >/dev/null
python3 "$root/scripts/pipeline/run-ledger.py" event run_contract_20260824-1200 completed \
  --emitter test --worktree "$tmp" \
  --payload '{"taskId":"spec-writer-1","role":"spec-writer"}' >/dev/null
python3 "$root/scripts/pipeline/run-ledger.py" event run_contract_20260824-1200 approved \
  --emitter test --worktree "$tmp" \
  --payload '{"gateId":"gate_spec","taskId":"spec-writer-1","aprobado_por":"test"}' >/dev/null
python3 "$root/scripts/pipeline/stage-guard.py" --role implementer \
  --run-id run_contract_20260824-1200 --worktree "$tmp" >/dev/null

python3 "$root/scripts/pipeline/codex-run.py" --role spec-writer \
  --prompt-file "$root/openspec/config.yaml" --worktree "$tmp" \
  --output-dir "$tmp/stage" --run-id run_contract_20260824-1200 \
  --codex-command "$tmp/fake-codex" >/dev/null
python3 - "$tmp/stage/result.json" <<'PY'
import json, sys
result = json.load(open(sys.argv[1], encoding="utf-8"))
assert result["status"] == "passed"
assert result["command"][4] == "workspace-write"
assert result["command"][6] == "gpt-5.6-luna"
PY

echo "runtime contract: PASS"
