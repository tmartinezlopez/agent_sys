#!/usr/bin/env bash
# Reanuda el vertical slice sobre el mismo ledger y worktree.
set -euo pipefail

run_id="${1:-}"
[ -n "$run_id" ] || { echo "uso: resume-run.sh <run_id> --worktree ruta [--codex-command comando] [--timeout segundos]" >&2; exit 1; }
shift
worktree="$(pwd)"
codex_command="codex"
timeout=""
while [ $# -gt 0 ]; do
  case "$1" in
    --worktree) worktree="${2:?--worktree requiere ruta}"; shift 2 ;;
    --codex-command) codex_command="${2:?--codex-command requiere comando}"; shift 2 ;;
    --timeout) timeout="${2:?--timeout requiere segundos}"; shift 2 ;;
    *) echo "argumento desconocido: $1" >&2; exit 1 ;;
  esac
done
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
worktree="$(cd "$worktree" && pwd)"
plan="$(python3 "$script_dir/run-ledger.py" resume-plan "$run_id" --worktree "$worktree")"
gate_status="$(python3 -c "import json,sys; p=json.load(sys.stdin); print(p['gates']['gate_spec']['status'])" <<<"$plan")"
resume_stage="$(python3 -c "import json,sys; print(json.load(sys.stdin).get('resumeStage') or '')" <<<"$plan")"
change="$(python3 -c "import json,sys; print(json.load(sys.stdin).get('change') or '')" <<<"$plan")"
[ "$gate_status" = approved ] || { echo "gate_spec no aprobado: $gate_status" >&2; exit 1; }
[ "$resume_stage" = implementer ] || { echo "resume-plan no apunta a implementer: $resume_stage" >&2; exit 1; }
[ -n "$change" ] || { echo "no se pudo derivar el change del ledger" >&2; exit 1; }

run_dir="$worktree/.pipeline/runs/$run_id"
stage_dir="$run_dir/stages/implementer"
mkdir -p "$stage_dir"
python3 "$script_dir/run-ledger.py" event "$run_id" run_resumed --emitter human \
  --worktree "$worktree" --payload "$(python3 - "$resume_stage" <<'PY'
import json, sys
print(json.dumps({"resumeStage": sys.argv[1], "midStage": False}))
PY
)"

python3 - "$stage_dir/prompt.md" "$change" "$worktree" <<'PY'
from pathlib import Path
import sys
path, change, worktree = sys.argv[1:]
Path(path).write_text(f'''Rol: implementer
Change OpenSpec: {change}
Directorio del change: {worktree}/openspec/changes/{change}
Checkout escribible: {worktree}

Implementa únicamente las tareas aprobadas de ese change en el checkout.
No crees otro change, no hagas commit ni push y deja evidencia reproducible.
En la respuesta final resume archivos modificados y verificaciones ejecutadas.
''', encoding="utf-8")
PY
payload="$(python3 - "$run_id" "$stage_dir" <<'PY'
import json, sys
print(json.dumps({"taskId":"implementer-1", "role":"implementer", "stageDir":sys.argv[2]}))
PY
)"
python3 "$script_dir/run-ledger.py" event "$run_id" dispatched --emitter runtime \
  --worktree "$worktree" --payload "$payload"
run_args=(python3 "$script_dir/codex-run.py" --role implementer --prompt-file "$stage_dir/prompt.md"
  --worktree "$worktree" --output-dir "$stage_dir" --run-id "$run_id"
  --codex-command "$codex_command")
[ -n "$timeout" ] && run_args+=(--timeout "$timeout")
"${run_args[@]}" >/dev/null
result_payload="$(python3 - "$stage_dir/result.json" <<'PY'
import json, sys
r = json.load(open(sys.argv[1], encoding="utf-8"))
print(json.dumps({"taskId":"implementer-1", "role":"implementer",
                  "resultFile":sys.argv[1], "exitCode":r.get("exitCode")}))
PY
)"
if python3 - "$stage_dir/result.json" <<'PY'
import json, sys
raise SystemExit(0 if json.load(open(sys.argv[1], encoding="utf-8"))["status"] == "passed" else 1)
PY
then
  python3 "$script_dir/run-ledger.py" event "$run_id" completed --emitter runtime \
    --worktree "$worktree" --payload "$result_payload"
  python3 "$script_dir/run-ledger.py" summary "$run_id" --worktree "$worktree" >/dev/null
  echo "RESUMED run_id=$run_id stage=implementer status=completed"
  exit 0
fi
python3 "$script_dir/run-ledger.py" event "$run_id" failed --emitter runtime \
  --worktree "$worktree" --payload "$result_payload"
echo "implementer falló: $run_id" >&2
exit 1
