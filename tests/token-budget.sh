#!/usr/bin/env bash
set -euo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
tmp="$(mktemp -d /tmp/reference-codex-token-XXXXXX)"
trap 'find "$tmp" -depth -type f -delete; find "$tmp" -depth -type d -empty -delete' EXIT
repo="$tmp/repo"
mkdir -p "$repo"
git -C "$repo" init -q -b main
prompt="$tmp/prompt.md"
printf 'prompt\n' > "$prompt"

fake="$tmp/fake-codex"
printf '%s\n' '#!/usr/bin/env bash' 'set -euo pipefail' 'printf "%s\n" '\''{"usage":{"input_tokens":7,"output_tokens":5,"output_tokens_details":{"reasoning_tokens":2},"input_tokens_details":{"cached_tokens":3}}}'\''' > "$fake"
chmod +x "$fake"
python3 "$root/scripts/pipeline/codex-run.py" --role reviewer \
  --prompt-file "$prompt" --worktree "$repo" --output-dir "$tmp/stage" \
  --run-id token-run --codex-command "$fake" >/dev/null
python3 - "$tmp/stage/usage.json" <<'PY'
import json
import sys

usage = json.load(open(sys.argv[1], encoding="utf-8"))
assert usage["status"] == "reported", usage
assert usage["totalTokens"] == 12, usage
assert usage["reasoningTokens"] == 2, usage
PY

python3 - "$root/scripts/pipeline/token-usage.py" <<'PY'
import importlib.util
import sys

spec = importlib.util.spec_from_file_location("token_usage", sys.argv[1])
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
full = module.normalize({
    "input_tokens": 7,
    "output_tokens": 5,
    "output_tokens_details": {"reasoning_tokens": 2},
    "input_tokens_details": {"cached_tokens": 3},
})
assert full == {
    "status": "reported", "source": "codex-json", "inputTokens": 7,
    "outputTokens": 5, "reasoningTokens": 2, "cachedInputTokens": 3,
    "totalTokens": 12,
}, full
unknown = module.unknown()
assert unknown["status"] == "unknown" and unknown["totalTokens"] is None
PY

python3 "$root/scripts/pipeline/run-ledger.py" init token_run --worktree "$repo" >/dev/null
python3 "$root/scripts/pipeline/run-ledger.py" event token_run completed --emitter test \
  --worktree "$repo" --payload '{"taskId":"reviewer-1","role":"reviewer","usage":{"status":"reported","totalTokens":7}}' >/dev/null
python3 "$root/scripts/pipeline/run-ledger.py" event token_run failed --emitter test \
  --worktree "$repo" --payload '{"taskId":"reviewer-1","role":"reviewer","usage":{"status":"reported","totalTokens":5}}' >/dev/null
python3 "$root/scripts/pipeline/run-ledger.py" event token_run completed --emitter test \
  --worktree "$repo" --payload '{"taskId":"qa-1","role":"qa","usage":{"status":"unknown","totalTokens":null}}' >/dev/null

python3 - "$repo/.pipeline/runs/token_run/current-state.json" <<'PY'
import json
import sys

state = json.load(open(sys.argv[1], encoding="utf-8"))
assert state["tokenUsage"] == {"totalTokens": 12, "unknownStages": 1}, state
PY

if PIPELINE_MAX_TOKENS=12 python3 "$root/scripts/pipeline/run-ledger.py" \
  dispatch-check token_run --worktree "$repo" >/dev/null 2>&1; then
  echo "se permitió superar el presupuesto de tokens" >&2
  exit 1
fi
PIPELINE_MAX_TOKENS=13 python3 "$root/scripts/pipeline/run-ledger.py" \
  dispatch-check token_run --worktree "$repo"

echo "token budget: PASS"
