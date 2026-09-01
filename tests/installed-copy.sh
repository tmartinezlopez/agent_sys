#!/usr/bin/env bash
set -euo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
tmp="$(mktemp -d /tmp/reference-codex-installed-XXXXXX)"
target="$tmp/consumer"
worktrees="$tmp/worktrees"
fake="$tmp/fake-codex"
worktree=""

cleanup() {
  if [ -n "$worktree" ] && [ -d "$worktree" ]; then
    git -C "$target" worktree remove --force "$worktree" >/dev/null 2>&1 || true
  fi
  git -C "$target" branch -D "feature/installed-copy" >/dev/null 2>&1 || true
  rm -rf "$tmp"
}
trap cleanup EXIT

# Construye un checkout consumidor, elimina el runtime heredado y lo instala
# de nuevo como haría un proyecto externo.
git clone --no-hardlinks "$root" "$target" >/dev/null
git -C "$target" config user.email codex-test@example.invalid
git -C "$target" config user.name codex-test
git -C "$target" rm -r -q scripts/pipeline
git -C "$target" commit -q -m 'consumer project without runtime'
mkdir -p "$worktrees"
"$root/scripts/pipeline/bootstrap.sh" "$target" \
  --source "$root/scripts/pipeline" >/dev/null
git -C "$target" add scripts/pipeline
git -C "$target" commit -q -m 'install pipeline runtime'

python3 - "$fake" <<'PY'
from pathlib import Path
import sys

Path(sys.argv[1]).write_text(r'''#!/usr/bin/env bash
set -euo pipefail

prompt="${!#}"
if [[ "$prompt" == *"Rol: spec-writer"* ]]; then
  change="$(printf '%s\n' "$prompt" | sed -n 's/^Nombre exacto del change: //p')"
  python3 - "$change" <<'PY2'
from pathlib import Path
import shutil
import sys

change = sys.argv[1]
shutil.copytree(
    Path("openspec/changes/archive/2026-08-25-reference-codex-runtime"),
    Path("openspec/changes") / change,
)
PY2
  printf 'AGENT_SYS_CHANGE: %s\n' "$change"
else
  printf 'fake stage completed\n'
fi
''', encoding="utf-8")
PY
chmod +x "$fake"

set +e
output="$(PIPELINE_WORKTREES_DIR="$worktrees" \
  "$target/scripts/pipeline/new-feature.sh" installed-copy \
  "validar runtime instalado" --no-tmux --codex-command "$fake" --timeout 30 2>&1)"
pipeline_rc=$?
set -e

[ "$pipeline_rc" -eq 2 ] || { echo "$output" >&2; exit 1; }
printf '%s\n' "$output" | grep -q '^GATE_PENDING run_id='
worktree="$(printf '%s\n' "$output" | sed -n 's/^GATE_PENDING run_id=[^ ]* worktree=//p')"
run_id="$(printf '%s\n' "$output" | sed -n 's/^GATE_PENDING run_id=\([^ ]*\) worktree=.*/\1/p')"
[ -d "$worktree/scripts/pipeline" ] && [ -n "$run_id" ]

"$worktree/scripts/pipeline/gate.sh" "$run_id" approve test --worktree "$worktree" >/dev/null
set +e
resume_output="$("$worktree/scripts/pipeline/resume-run.sh" "$run_id" \
  --worktree "$worktree" --codex-command "$fake" --timeout 30 2>&1)"
resume_rc=$?
set -e
[ "$resume_rc" -eq 2 ]
printf '%s\n' "$resume_output" | grep -q "GATE_PENDING gate=gate_release run_id=$run_id"

"$worktree/scripts/pipeline/gate.sh" "$run_id" approve test-final \
  --gate gate_release --worktree "$worktree" >/dev/null
[ "$("$worktree/scripts/pipeline/resume-run.sh" "$run_id" \
  --worktree "$worktree" --codex-command "$fake" --timeout 30)" = \
  "COMPLETED run_id=$run_id status=completed" ]

python3 - "$target" "$worktree" "$run_id" <<'PY'
import json
from pathlib import Path
import sys

target, worktree, run_id = map(Path, sys.argv[1:])
run_dir = worktree / ".pipeline" / "runs" / run_id
state = json.loads((run_dir / "current-state.json").read_text(encoding="utf-8"))
events = [json.loads(line) for line in (run_dir / "events.jsonl").read_text(encoding="utf-8").splitlines()]
roles = [event.get("role") for event in events if event.get("type") == "dispatched"]
assert state["status"] == "completed", state
assert roles == ["spec-writer", "implementer", "test-runner", "reviewer", "qa"], roles
assert (run_dir / "summary.json").is_file()
assert not list(target.glob(".pipeline/runs/*"))
assert target.joinpath(".git/HEAD").read_text(encoding="utf-8").strip() != "ref: refs/heads/feature/installed-copy"
PY

echo "installed copy: PASS"
