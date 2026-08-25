#!/usr/bin/env bash
set -euo pipefail

root="$(cd "$(dirname "$BASH_SOURCE")/.." && pwd)"
tmp="$(mktemp -d /tmp/reference-codex-full-XXXXXX)"
fake="$tmp/fake-codex"
retry_marker="$tmp/retry-marker"

python3 - "$fake" "$retry_marker" <<'PY'
from pathlib import Path
import sys

path, marker = sys.argv[1:]
Path(path).write_text(f'''#!/usr/bin/env bash
set -euo pipefail
case "${{FAKE_MODE:-pass}}" in
  retry)
    if [[ "$*" == *"Rol: reviewer"* ]] && [ ! -e "{marker}" ]; then
      touch "{marker}"
      exit 9
    fi
    ;;
  timeout)
    [[ "$*" == *"Rol: reviewer"* ]] && sleep 2
    ;;
esac
exit 0
''', encoding="utf-8")
PY
chmod +x "$fake"

seed_run() {
  local name="$1" ui="$2" repo="$tmp/$1"
  mkdir -p "$repo"
  git -C "$repo" init -q -b main
  if [ "$ui" = 1 ]; then
    python3 "$root/scripts/pipeline/run-ledger.py" init "$name" --worktree "$repo" --ui >/dev/null
  else
    python3 "$root/scripts/pipeline/run-ledger.py" init "$name" --worktree "$repo" >/dev/null
  fi
  python3 "$root/scripts/pipeline/run-ledger.py" event "$name" dispatched \
    --emitter test --worktree "$repo" \
    --payload '{"taskId":"spec-writer-1","role":"spec-writer","change":"test-change"}' >/dev/null
  python3 "$root/scripts/pipeline/run-ledger.py" event "$name" completed \
    --emitter test --worktree "$repo" \
    --payload '{"taskId":"spec-writer-1","role":"spec-writer"}' >/dev/null
  python3 "$root/scripts/pipeline/run-ledger.py" event "$name" gate_opened \
    --emitter test --worktree "$repo" \
    --payload '{"gateId":"gate_spec","taskId":"spec-writer-1"}' >/dev/null
  python3 "$root/scripts/pipeline/run-ledger.py" event "$name" approved \
    --emitter test --worktree "$repo" \
    --payload '{"gateId":"gate_spec","taskId":"spec-writer-1","aprobado_por":"test"}' >/dev/null
}

run_until_release() {
  local name="$1" repo="$tmp/$1" expected_roles="$2"
  set +e
  output="$("$root/scripts/pipeline/resume-run.sh" "$name" --worktree "$repo" \
    --codex-command "$fake" --timeout 30 2>&1)"
  rc=$?
  set -e
  [ "$rc" -eq 2 ]
  printf '%s\n' "$output" | grep -q "GATE_PENDING gate=gate_release run_id=$name"
  python3 - "$repo" "$expected_roles" <<'PY'
import json
import sys
from pathlib import Path

repo, expected = sys.argv[1:]
events = [json.loads(line) for line in
          (Path(repo)/'.pipeline/runs'/Path(repo).name/'events.jsonl').read_text().splitlines()]
roles = [event.get('role') for event in events if event.get('type') == 'dispatched']
assert roles == expected.split(','), roles
PY
}

seed_run run_full 0
run_until_release run_full spec-writer,implementer,test-runner,reviewer,qa
full_repo="$tmp/run_full"
bash "$root/scripts/pipeline/gate.sh" run_full approve test-final --gate gate_release --worktree "$full_repo" >/dev/null
[ "$("$root/scripts/pipeline/resume-run.sh" run_full --worktree "$full_repo" --codex-command "$fake")" = "COMPLETED run_id=run_full status=completed" ]

seed_run run_ui 1
run_until_release run_ui spec-writer,implementer,test-runner,reviewer,ui-reviewer,qa

seed_run run_retry 0
set +e
FAKE_MODE=retry "$root/scripts/pipeline/resume-run.sh" run_retry --worktree "$tmp/run_retry" \
  --codex-command "$fake" --timeout 30 >/dev/null 2>&1
retry_rc=$?
set -e
[ "$retry_rc" -eq 1 ]
run_until_release run_retry spec-writer,implementer,test-runner,reviewer,reviewer,qa

seed_run run_timeout 0
set +e
FAKE_MODE=timeout "$root/scripts/pipeline/resume-run.sh" run_timeout --worktree "$tmp/run_timeout" \
  --codex-command "$fake" --timeout 0.1 >/dev/null 2>&1
timeout_rc=$?
set -e
[ "$timeout_rc" -eq 1 ]
python3 - "$tmp/run_timeout" <<'PY'
import json
import sys
from pathlib import Path
result = json.loads((Path(sys.argv[1])/'.pipeline/runs/run_timeout/stages/reviewer/result.json').read_text())
assert result['exitCode'] == 124, result
PY

echo "full pipeline: PASS"
