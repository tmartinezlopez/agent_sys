#!/usr/bin/env bash
# Registra la decisión humana del gate del spec. No reanuda el run.
set -euo pipefail

run_id="${1:-}"
decision="${2:-}"
operator="${3:-}"
[ -n "$run_id" ] && [ -n "$decision" ] && [ -n "$operator" ] || {
  echo "uso: gate.sh <run_id> <approve|changes|discard> <operator> [reason] --worktree ruta" >&2
  exit 1
}
shift 3
reason=""
worktree="$(pwd)"
while [ $# -gt 0 ]; do
  case "$1" in
    --worktree) worktree="${2:?--worktree requiere ruta}"; shift 2 ;;
    *) [ -z "$reason" ] || { echo "argumento desconocido: $1" >&2; exit 1; }; reason="$1"; shift ;;
  esac
done
case "$decision" in approve|changes|discard) ;; *) echo "decisión inválida" >&2; exit 1 ;; esac
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
state="$(python3 "$script_dir/run-ledger.py" show "$run_id" --worktree "$worktree")"
gate_status="$(python3 -c "import json,sys; s=json.load(sys.stdin); print(next(g['status'] for g in s['gates'] if g['gateId'] == 'gate_spec'))" <<<"$state")"
[ "$gate_status" = pending ] || { echo "gate_spec ya está decidido: $gate_status" >&2; exit 1; }
payload="$(python3 - "$operator" "$reason" <<'PY'
import json, sys
operator, reason = sys.argv[1:]
print(json.dumps({"gateId":"gate_spec", "taskId":"spec-writer-1",
                  "aprobado_por":operator, "reason":reason or None}))
PY
)"
case "$decision" in
  approve) event=approved ;;
  discard) event=rejected ;;
  changes) event=changes_requested ;;
esac
python3 "$script_dir/run-ledger.py" event "$run_id" "$event" --emitter human \
  --worktree "$worktree" --payload "$payload"
echo "gate_spec=$decision run_id=$run_id operator=$operator"
