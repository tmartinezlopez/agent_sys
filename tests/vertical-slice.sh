#!/usr/bin/env bash
set -euo pipefail

root="$(cd "$(dirname "$BASH_SOURCE")/.." && pwd)"
tmp="$(mktemp -d /tmp/reference-codex-slice-XXXXXX)"
item="slice-feature"
worktrees="$tmp/worktrees"
fake="$tmp/fake-codex"
worktree=""

cleanup() {
  if [ -n "$worktree" ] && [ -d "$worktree" ]; then
    git -C "$root" worktree remove --force "$worktree" >/dev/null 2>&1 || true
  fi
  git -C "$root" branch -D "feature/$item" >/dev/null 2>&1 || true
}
trap cleanup EXIT

python3 - "$fake" <<'PY'
from pathlib import Path
import sys

Path(sys.argv[1]).write_text(r'''#!/usr/bin/env bash
set -euo pipefail
prompt="$*"
if [[ "$prompt" == *"Rol: spec-writer"* ]]; then
  change="$(printf '%s\n' "$prompt" | sed -n 's/^Nombre exacto del change: //p')"
  python3 - "$change" <<'PY2'
from pathlib import Path
import shutil
import sys

change = sys.argv[1]
source = Path("openspec/changes/reference-codex-runtime")
target = Path("openspec/changes") / change
shutil.copytree(source, target)
PY2
  printf 'AGENT_SYS_CHANGE: %s\n' "$change"
else
  printf 'fake implementer completed\n'
fi
''', encoding="utf-8")
PY
chmod +x "$fake"
mkdir -p "$worktrees"

set +e
output="$(PIPELINE_WORKTREES_DIR="$worktrees" \
  "$root/scripts/pipeline/new-feature.sh" "$item" "probar slice vertical" \
  --no-tmux --codex-command "$fake" --timeout 30 2>&1)"
pipeline_rc=$?
set -e

[ "$pipeline_rc" -eq 2 ] || { echo "se esperaba gate pendiente (rc=2), rc=$pipeline_rc" >&2; echo "$output" >&2; exit 1; }
printf '%s\n' "$output" | grep -q '^GATE_PENDING run_id=' || { echo "$output" >&2; exit 1; }
worktree="$(printf '%s\n' "$output" | sed -n 's/^GATE_PENDING run_id=[^ ]* worktree=//p')"
run_id="$(printf '%s\n' "$output" | sed -n 's/^GATE_PENDING run_id=\([^ ]*\) worktree=.*/\1/p')"
[ -d "$worktree" ] && [ -n "$run_id" ] || { echo "no se derivó worktree/run_id" >&2; exit 1; }

"$worktree/scripts/pipeline/gate.sh" "$run_id" approve test --worktree "$worktree" >/dev/null
resume_output="$("$worktree/scripts/pipeline/resume-run.sh" "$run_id" \
  --worktree "$worktree" --codex-command "$fake" --timeout 30)"
printf '%s\n' "$resume_output" | grep -q "RESUMED run_id=$run_id stage=implementer status=completed"

python3 - "$worktree" "$run_id" <<'PY'
import json
from pathlib import Path
import sys

worktree, run_id = sys.argv[1:]
run_dir = Path(worktree) / ".pipeline" / "runs" / run_id
state = json.loads((run_dir / "current-state.json").read_text(encoding="utf-8"))
events = [json.loads(line) for line in (run_dir / "events.jsonl").read_text(encoding="utf-8").splitlines()]
roles = [event.get("role") for event in events if event.get("type") == "dispatched"]
assert state["status"] == "completed", state
assert {task["role"] for task in state["tasks"]} == {"spec-writer", "implementer"}, state
assert roles.count("spec-writer") == 1, roles
assert roles.count("implementer") == 1, roles
assert sum(event.get("type") == "run_resumed" for event in events) == 1, events
assert json.loads((run_dir / "summary.json").read_text(encoding="utf-8"))["status"] == "completed"
PY

echo "vertical slice: PASS"
