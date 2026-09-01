#!/usr/bin/env bash
set -euo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
tmp="$(mktemp -d /tmp/reference-codex-contract-XXXXXX)"
trap 'rm -rf "$tmp"' EXIT

printf '#!/usr/bin/env bash\nprintf "fake codex\\n"\n' > "$tmp/fake-codex"
chmod +x "$tmp/fake-codex"

python3 - "$root/scripts/pipeline/roles.json" <<'PY'
import json
import sys

roles = json.load(open(sys.argv[1], encoding="utf-8"))
expected = {
    "spec-writer": ("gpt-5.6-luna", "medium"),
    "implementer": ("gpt-5.6-luna", "low"),
    "test-runner": ("gpt-5.6-luna", "medium"),
    "reviewer": ("gpt-5.6-luna", "medium"),
    "ui-reviewer": ("gpt-5.6-luna", "low"),
    "qa": ("gpt-5.6-luna", "low"),
}
assert {name: (data["model"], data["reasoning"]) for name, data in roles.items()} == expected
PY

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
assert "--dangerously-bypass-approvals-and-sandbox" in result["command"]
assert result["command"][5] == "gpt-5.6-luna"
PY

for launcher in launch-spec-writer.sh launch-implementer.sh launch-test-runner.sh \
  launch-reviewer.sh launch-ui-reviewer.sh launch-qa.sh; do
  [ -x "$root/scripts/pipeline/roles/$launcher" ]
done

if PIPELINE_MAX_DISPATCHES=1 python3 "$root/scripts/pipeline/run-ledger.py" \
  dispatch-check run_contract_20260824-1200 --worktree "$tmp"; then
  echo "se permitió superar el presupuesto de despachos" >&2
  exit 1
fi

python3 "$root/scripts/pipeline/codex-run.py" --role spec-writer \
  --prompt-file "$root/openspec/config.yaml" --worktree "$tmp" \
  --output-dir "$tmp/blocked-real" --run-id run_contract_20260824-1200 \
  --codex-command codex >/dev/null
python3 - "$tmp/blocked-real/result.json" <<'PY'
import json
import sys
result = json.load(open(sys.argv[1], encoding="utf-8"))
assert result["exitCode"] == 126, result
PY

echo "runtime contract: PASS"
