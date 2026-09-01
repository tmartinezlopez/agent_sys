#!/usr/bin/env bash
# Ejecuta el vertical slice spec-writer -> gate dentro de un worktree.
set -euo pipefail

usage() {
  echo "uso: run-pipeline.sh <item> <objetivo> [--worktree ruta] [--run-id id] [--ui] [--codex-command comando] [--timeout segundos]" >&2
  exit 1
}

item="${1:-}"
objective="${2:-}"
[ -n "$item" ] && [ -n "$objective" ] || usage
shift 2
worktree="$(pwd)"
run_id=""
codex_command="codex"
timeout=""
ui=0
while [ $# -gt 0 ]; do
  case "$1" in
    --worktree) worktree="${2:?--worktree requiere ruta}"; shift 2 ;;
    --run-id) run_id="${2:?--run-id requiere id}"; shift 2 ;;
    --ui) ui=1; shift ;;
    --codex-command) codex_command="${2:?--codex-command requiere comando}"; shift 2 ;;
    --timeout) timeout="${2:?--timeout requiere segundos}"; shift 2 ;;
    *) echo "argumento desconocido: $1" >&2; exit 1 ;;
  esac
done

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
worktree="$(cd "$worktree" && pwd)"
[ -d "$worktree/.git" ] || [ -f "$worktree/.git" ] || { echo "no es un checkout Git: $worktree" >&2; exit 1; }
preflight_args=("$script_dir/preflight.sh" --worktree "$worktree")
[ "$(basename "$codex_command")" = codex ] && preflight_args+=(--real)
"${preflight_args[@]}" >/dev/null
timestamp="$(date -u +%Y%m%d-%H%M%S)"
run_id="${run_id:-run_${item}_${timestamp}_$$}"
change_name="agent-sys-${item}-${timestamp}-$$"
run_dir="$worktree/.pipeline/runs/$run_id"
stage_dir="$run_dir/stages/spec-writer"
mkdir -p "$stage_dir"

if [ -f "$run_dir/run.json" ] && ! python3 "$script_dir/run-ledger.py" dispatch-check "$run_id" \
    --worktree "$worktree"; then
  echo "no se puede continuar el run: presupuesto agotado" >&2
  exit 1
fi

init_args=(python3 "$script_dir/run-ledger.py" init "$run_id" --worktree "$worktree")
[ "$ui" -eq 1 ] && init_args+=(--ui)
"${init_args[@]}"
python3 - "$stage_dir/prompt.md" "$change_name" "$objective" "$script_dir" <<'PY'
from pathlib import Path
import sys
path, change, objective, script_dir = sys.argv[1:]
guide = Path(script_dir).parents[1] / "GUIA-USO.md"
Path(path).write_text(f'''Rol: spec-writer
Antes de actuar, lee las instrucciones de {guide} si existe.
Objetivo del run: {objective}
Nombre exacto del change: {change}

Crea el change OpenSpec real con:
openspec new change "{change}"
Completa proposal.md, al menos un spec en specs/, design.md y tasks.md.
No implementes código de producto. No uses un rol genérico ni inventes una
configuración. Valida al final con:
openspec validate "{change}" --strict

Tu respuesta final debe incluir exactamente:
AGENT_SYS_CHANGE: {change}
Después resume artefactos y validación.
''', encoding="utf-8")
PY

run_args=("$script_dir/roles/launch-spec-writer.sh" "$run_id"
  --worktree "$worktree" --change "$change_name" --codex-command "$codex_command")
[ -n "$timeout" ] && run_args+=(--timeout "$timeout")
real_codex=0
[ "$(basename "$codex_command")" = codex ] && real_codex=1
if [ "$real_codex" -eq 1 ]; then
  PIPELINE_PRESERVE_PROMPT=1 "${run_args[@]}" --tmux \
    --tmux-session "$(basename "$worktree")-coordinator" >/dev/null
  echo "GATE_PENDING run_id=$run_id worktree=$worktree"
  exit 2
fi
PIPELINE_PRESERVE_PROMPT=1 "${run_args[@]}" >/dev/null

result_payload="$(python3 - "$stage_dir/result.json" "$change_name" <<'PY'
import json, sys
r = json.load(open(sys.argv[1], encoding="utf-8"))
print(json.dumps({"taskId":"spec-writer-1", "role":"spec-writer",
                  "resultFile":sys.argv[1], "exitCode":r.get("exitCode"),
                  "change":sys.argv[2]}))
PY
)"
if python3 - "$stage_dir/result.json" <<'PY'
import json, sys
raise SystemExit(0 if json.load(open(sys.argv[1], encoding="utf-8"))["status"] == "passed" else 1)
PY
then
  if ! python3 "$script_dir/validate-spec.py" --worktree "$worktree" --stage-dir "$stage_dir" >/dev/null; then
    python3 "$script_dir/run-ledger.py" event "$run_id" failed --emitter runtime --worktree "$worktree" \
      --payload "$result_payload"
    echo "spec-writer falló la validación: $run_id" >&2
    exit 1
  fi
  python3 "$script_dir/run-ledger.py" event "$run_id" completed --emitter runtime \
    --worktree "$worktree" --payload "$result_payload"
  gate_payload='{"gateId":"gate_spec","taskId":"spec-writer-1","role":"spec-writer"}'
  python3 "$script_dir/run-ledger.py" event "$run_id" gate_opened --emitter runtime \
    --worktree "$worktree" --payload "$gate_payload"
  echo "GATE_PENDING run_id=$run_id worktree=$worktree"
  exit 2
fi
python3 "$script_dir/run-ledger.py" event "$run_id" failed --emitter runtime \
  --worktree "$worktree" --payload "$result_payload"
echo "spec-writer falló: $run_id" >&2
exit 1
