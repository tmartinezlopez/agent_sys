#!/usr/bin/env bash
# Ejecuta una etapa declarada y persiste toda su evidencia en el run.
set -euo pipefail

run_id="${1:-}"
role="${2:-}"
[ -n "$run_id" ] && [ -n "$role" ] || {
  echo "uso: run-stage.sh <run_id> <role> --worktree ruta [--change nombre] [--codex-command comando] [--timeout segundos]" >&2
  exit 1
}
shift 2
worktree="$(pwd)"
change=""
codex_command="codex"
timeout=""
while [ $# -gt 0 ]; do
  case "$1" in
    --worktree) worktree="${2:?--worktree requiere ruta}"; shift 2 ;;
    --change) change="${2:?--change requiere nombre}"; shift 2 ;;
    --codex-command) codex_command="${2:?--codex-command requiere comando}"; shift 2 ;;
    --timeout) timeout="${2:?--timeout requiere segundos}"; shift 2 ;;
    *) echo "argumento desconocido: $1" >&2; exit 1 ;;
  esac
done

script_dir="${PIPELINE_SCRIPT_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)}"
worktree="$(cd "$worktree" && pwd)"
run_dir="$worktree/.pipeline/runs/$run_id"
stage_dir="$run_dir/stages/$role"
mkdir -p "$stage_dir"

if ! budget_error="$(python3 "$script_dir/run-ledger.py" dispatch-check "$run_id" \
    --worktree "$worktree" 2>&1)"; then
  anomaly_payload="$(python3 - "$role" "$budget_error" <<'PY'
import json, sys
role, reason = sys.argv[1:]
print(json.dumps({"role": role, "reason": reason, "stage": role,
                  "kind": "token_budget_exhausted" if "tokens" in reason else "dispatch_budget_exhausted"}))
PY
)"
  python3 "$script_dir/run-ledger.py" event "$run_id" anomaly --emitter runtime \
    --worktree "$worktree" --payload "$anomaly_payload" >/dev/null
  echo "$budget_error" >&2
  exit 1
fi

guard_error=""
if ! guard_error="$(python3 "$script_dir/stage-guard.py" --role "$role" \
    --run-id "$run_id" --worktree "$worktree" 2>&1)"; then
  anomaly_payload="$(python3 - "$role" "$guard_error" <<'PY'
import json, sys
role, reason = sys.argv[1:]
print(json.dumps({"role": role, "reason": reason, "stage": role}))
PY
)"
  python3 "$script_dir/run-ledger.py" event "$run_id" anomaly --emitter runtime \
    --worktree "$worktree" --payload "$anomaly_payload" >/dev/null
  echo "$guard_error" >&2
  exit 1
fi

python3 - "$stage_dir/prompt.md" "$role" "$change" "$worktree" "$script_dir" <<'PY'
from pathlib import Path
import os
import sys

path, role, change, worktree, script_dir = sys.argv[1:]
guide = Path(script_dir).parents[1] / "GUIA-USO.md"
common = f'''Rol: {role}
Change OpenSpec: {change or "no especificado"}
Checkout: {worktree}
Antes de actuar, lee las instrucciones de {guide} si existe.

Trabaja únicamente dentro del checkout indicado. No hagas commit, merge, push
ni publicación automática. Deja evidencia reproducible y resume verificaciones
en tu respuesta final.
'''
instructions = {
    "spec-writer": f'''Genera o completa la especificación OpenSpec del change
{change} en {worktree}/openspec/changes/{change}. No implementes código de
producto. Valida los artefactos con openspec validate --strict.
''',
    "implementer": f'''Implementa únicamente las tareas aprobadas del change
OpenSpec en {worktree}/openspec/changes/{change}. Ejecuta las verificaciones
relevantes y modifica sólo el código necesario.
''',
    "test-runner": '''Ejecuta la batería de pruebas relevante para el cambio y
analiza sus resultados. Este rol es read-only: no modifiques archivos. Si una
prueba falla, deja el diagnóstico exacto y los comandos reproducibles.
''',
    "reviewer": '''Revisa el diff, el change OpenSpec y los contratos del
runtime. Este rol es read-only: no modifiques archivos. Identifica defectos,
regresiones, riesgos y verificaciones faltantes con severidad explícita.
''',
    "ui-reviewer": '''Revisa específicamente la parte de interfaz del cambio,
sus estados, accesibilidad y consistencia visual disponible en el checkout.
Este rol es read-only: no modifiques archivos. Si no hay evidencia suficiente,
decláralo en vez de inventar una aprobación.
''',
    "qa": '''Realiza la validación de aceptación del cambio completo usando
las pruebas y contratos disponibles. Este rol es read-only: no modifiques
archivos. Reporta PASS o FAIL, evidencia y cualquier bloqueo residual.
''',
}
if os.environ.get("PIPELINE_PRESERVE_PROMPT") != "1" or not Path(path).exists():
    Path(path).write_text(common + "\n" + instructions.get(role, ""), encoding="utf-8")
PY

payload="$(python3 - "$role" "$stage_dir" "$change" <<'PY'
import json, sys
role, stage_dir, change = sys.argv[1:]
print(json.dumps({"taskId": f"{role}-1", "role": role,
                  "stageDir": stage_dir, "change": change or None}))
PY
)"
python3 "$script_dir/run-ledger.py" event "$run_id" dispatched --emitter runtime \
  --worktree "$worktree" --payload "$payload"

run_args=(python3 "$script_dir/codex-run.py" --role "$role" --prompt-file "$stage_dir/prompt.md"
  --worktree "$worktree" --output-dir "$stage_dir" --run-id "$run_id"
  --codex-command "$codex_command")
[ -n "$timeout" ] && run_args+=(--timeout "$timeout")
"${run_args[@]}" >/dev/null

result_payload="$(python3 - "$stage_dir/result.json" "$role" "$stage_dir" "$change" <<'PY'
import json, sys
result_path, role, stage_dir, change = sys.argv[1:]
result = json.load(open(result_path, encoding="utf-8"))
print(json.dumps({"taskId": f"{role}-1", "role": role,
                  "stageDir": stage_dir, "resultFile": result_path,
                  "exitCode": result.get("exitCode"), "usage": result.get("usage"),
                  "change": change or None}))
PY
)"
if python3 - "$stage_dir/result.json" <<'PY'
import json, sys
raise SystemExit(0 if json.load(open(sys.argv[1], encoding="utf-8"))["status"] == "passed" else 1)
PY
then
  python3 "$script_dir/run-ledger.py" event "$run_id" completed --emitter runtime \
    --worktree "$worktree" --payload "$result_payload"
  echo "STAGE_COMPLETED run_id=$run_id stage=$role"
  exit 0
fi
python3 "$script_dir/run-ledger.py" event "$run_id" failed --emitter runtime \
  --worktree "$worktree" --payload "$result_payload"
echo "stage failed: $role" >&2
exit 1
