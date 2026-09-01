#!/usr/bin/env bash
set -euo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
tmp="$(mktemp -d /tmp/reference-codex-cache-XXXXXX)"
trap 'find "$tmp" -depth -type f -delete; find "$tmp" -depth -type d -empty -delete' EXIT
repo="$tmp/repo"
mkdir -p "$repo"
git -C "$repo" init -q -b main
git -C "$repo" config user.email test@example.invalid
git -C "$repo" config user.name test
printf 'tracked\n' > "$repo/file.txt"
git -C "$repo" add file.txt && git -C "$repo" commit -qm init
printf 'prompt\n' > "$tmp/prompt.md"
count="$tmp/count"
fake="$tmp/fake-codex"
printf '%s\n' '#!/usr/bin/env bash' 'set -euo pipefail' 'n=0' '[ -f "$COUNT_FILE" ] && n=$(<"$COUNT_FILE")' 'n=$((n + 1))' 'printf "%s" "$n" > "$COUNT_FILE"' 'printf "%s\n" '\''{"type":"result","usage":{"input_tokens":3,"output_tokens":2}}'\''' > "$fake"
chmod +x "$fake"

run() {
  local out="$1"
  COUNT_FILE="$count" PIPELINE_PROMPT_CACHE_MODE=read-write PIPELINE_PROMPT_CACHE_DIR="$tmp/cache" \
    python3 "$root/scripts/pipeline/codex-run.py" --role reviewer \
      --prompt-file "$tmp/prompt.md" --worktree "$repo" --output-dir "$out" \
      --run-id cache-test --codex-command "$fake" >/dev/null
}
run "$tmp/first"
run "$tmp/second"
python3 - "$tmp/first/result.json" "$tmp/second/result.json" "$count" "$tmp/cache" <<'PY'
import json
import pathlib
import sys

first, second, count, cache_dir = sys.argv[1:]
a = json.load(open(first, encoding="utf-8"))
b = json.load(open(second, encoding="utf-8"))
assert a["cacheDecision"]["decision"] == "cache_miss", a
assert a["cacheDecision"]["stored"] is True, a
assert b["cacheDecision"]["decision"] == "cache_hit", b
assert open(count, encoding="utf-8").read() == "1"
cache_file = next(pathlib.Path(cache_dir).glob("*.json"))
assert "prompt" not in cache_file.read_text(encoding="utf-8")
PY

printf 'changed prompt\n' > "$tmp/prompt.md"
run "$tmp/changed"
python3 - "$tmp/changed/result.json" "$count" <<'PY'
import json
import sys

result = json.load(open(sys.argv[1], encoding="utf-8"))
assert result["cacheDecision"]["decision"] == "cache_miss", result
assert open(sys.argv[2], encoding="utf-8").read() == "2"
PY

PIPELINE_PROMPT_CACHE_MODE=read-write PIPELINE_PROMPT_CACHE_DIR="$tmp/cache" \
  python3 "$root/scripts/pipeline/prompt-cache.py" clear --worktree "$repo" --force >/dev/null
[ -z "$(find "$tmp/cache" -type f -name '*.json' -print -quit 2>/dev/null)" ]
run "$tmp/after-clear"
python3 - "$tmp/after-clear/result.json" "$count" <<'PY'
import json
import sys

result = json.load(open(sys.argv[1], encoding="utf-8"))
assert result["cacheDecision"]["decision"] == "cache_miss", result
assert open(sys.argv[2], encoding="utf-8").read() == "3"
PY

if PIPELINE_PROMPT_CACHE_MODE=invalid python3 "$root/scripts/pipeline/codex-run.py" \
  --role reviewer --prompt-file "$tmp/prompt.md" --worktree "$repo" \
  --output-dir "$tmp/invalid" --run-id cache-test --codex-command "$fake" >/dev/null 2>&1; then
  echo "se aceptó modo de caché inválido" >&2
  exit 1
fi

COUNT_FILE="$count" PIPELINE_PROMPT_CACHE_MODE=read-write PIPELINE_PROMPT_CACHE_DIR="$tmp/cache" \
  python3 "$root/scripts/pipeline/codex-run.py" --role implementer \
    --prompt-file "$tmp/prompt.md" --worktree "$repo" --output-dir "$tmp/writer" \
    --run-id cache-test --codex-command "$fake" >/dev/null
python3 - "$tmp/writer/result.json" <<'PY'
import json
import sys

result = json.load(open(sys.argv[1], encoding="utf-8"))
assert result["cacheDecision"]["decision"] == "cache_bypass"
assert result["cacheDecision"]["reason"] == "role_not_read_only"
PY

echo "prompt cache: PASS"
