#!/usr/bin/env bash
set -euo pipefail

root="$(cd "$(dirname "$0")/.." && pwd)"
tmp="$(mktemp -d /tmp/reference-codex-guard-XXXXXX)"
repo="$tmp/repo"
mkdir -p "$repo"
git -C "$repo" init -q -b feature/guard-check
git -C "$repo" config user.email codex-test@example.invalid
git -C "$repo" config user.name codex-test
printf 'prompt\n' > "$tmp/prompt.md"
fake="$tmp/fake-codex"
cat > "$fake" <<'FAKE'
#!/usr/bin/env bash
set -euo pipefail
set +e
git push origin feature/guard-check >push.out 2>&1
push_rc=$?
git merge main >merge.out 2>&1
merge_rc=$?
git branch --show-current >branch.out
[ "$push_rc" -ne 0 ] && [ "$merge_rc" -ne 0 ]
FAKE
chmod +x "$fake"

python3 "$root/scripts/pipeline/codex-run.py" --role implementer \
  --prompt-file "$tmp/prompt.md" --worktree "$repo" \
  --output-dir "$tmp/stage" --run-id run_guard \
  --codex-command "$fake" >/dev/null
python3 - "$tmp/stage/result.json" <<'PY'
import json
import sys
result = json.load(open(sys.argv[1], encoding="utf-8"))
assert result["status"] == "passed", result
assert result["gitGuard"] == "merge-push-blocked"
PY
grep -q 'runtime bloqueado' "$repo/push.out"
grep -q 'runtime bloqueado' "$repo/merge.out"
grep -qx 'feature/guard-check' "$repo/branch.out"

echo "runtime integration guard: PASS"
