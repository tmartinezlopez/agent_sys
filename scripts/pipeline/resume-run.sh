#!/usr/bin/env bash
# Reanuda un run desde la primera etapa abierta o pendiente.
set -euo pipefail

run_id="${1:-}"
[ -n "$run_id" ] || {
  echo "uso: resume-run.sh <run_id> --worktree ruta [--codex-command comando] [--timeout segundos]" >&2
  exit 1
}
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

if [ -z "${PIPELINE_RESUME_SNAPSHOT:-}" ]; then
  runtime_dir="$worktree/.pipeline/runs/$run_id/runtime"
  mkdir -p "$runtime_dir"
  snapshot="$runtime_dir/resume-run.sh"
  cp "$script_dir/resume-run.sh" "$snapshot"
  reexec_args=("$run_id" --worktree "$worktree" --codex-command "$codex_command")
  [ -n "$timeout" ] && reexec_args+=(--timeout "$timeout")
  export PIPELINE_RESUME_SNAPSHOT=1
  export PIPELINE_SCRIPT_DIR="$script_dir"
  exec bash "$snapshot" "${reexec_args[@]}"
fi

plan_cmd=(python3 "$script_dir/run-ledger.py" resume-plan "$run_id" --worktree "$worktree")

plan="$("${plan_cmd[@]}")"
gate_spec="$(python3 -c "import json,sys; print(json.load(sys.stdin)['gates']['gate_spec']['status'])" <<<"$plan")"
resume_stage="$(python3 -c "import json,sys; print(json.load(sys.stdin).get('resumeStage') or '')" <<<"$plan")"
change="$(python3 -c "import json,sys; print(json.load(sys.stdin).get('change') or '')" <<<"$plan")"
[ "$gate_spec" = approved ] || {
  echo "gate_spec no aprobado: $gate_spec" >&2
  exit 1
}
[ -n "$change" ] || {
  echo "no se pudo derivar el change del ledger" >&2
  exit 1
}

if [ "$resume_stage" = gate_release ]; then
  release_status="$(python3 -c "import json,sys; print(json.load(sys.stdin)['gates']['gate_release']['status'])" <<<"$plan")"
  if [ "$release_status" = pending ]; then
    echo "GATE_PENDING gate=gate_release run_id=$run_id worktree=$worktree"
    exit 2
  fi
  echo "gate_release no aprobado: $release_status" >&2
  exit 1
fi

if [ -z "$resume_stage" ]; then
  python3 "$script_dir/run-ledger.py" summary "$run_id" --worktree "$worktree" >/dev/null
  echo "COMPLETED run_id=$run_id status=completed"
  exit 0
fi

if [ "$resume_stage" = spec-writer ]; then
  echo "spec-writer aún no ha terminado; usa run-pipeline.sh para iniciar el run" >&2
  exit 1
fi

python3 "$script_dir/run-ledger.py" event "$run_id" run_resumed --emitter human \
  --worktree "$worktree" --payload "$(python3 - "$resume_stage" <<'PY'
import json, sys
print(json.dumps({"resumeStage": sys.argv[1], "midStage": True}))
PY
)"

while :; do
  plan="$("${plan_cmd[@]}")"
  resume_stage="$(python3 -c "import json,sys; print(json.load(sys.stdin).get('resumeStage') or '')" <<<"$plan")"
  change="$(python3 -c "import json,sys; print(json.load(sys.stdin).get('change') or '')" <<<"$plan")"
  if [ "$resume_stage" = gate_release ]; then
    python3 "$script_dir/run-ledger.py" event "$run_id" gate_opened --emitter runtime \
      --worktree "$worktree" --payload '{"gateId":"gate_release","taskId":"qa-1","role":"qa"}' >/dev/null
    echo "GATE_PENDING gate=gate_release run_id=$run_id worktree=$worktree"
    exit 2
  fi
  if [ -z "$resume_stage" ]; then
    python3 "$script_dir/run-ledger.py" summary "$run_id" --worktree "$worktree" >/dev/null
    echo "COMPLETED run_id=$run_id status=completed"
    exit 0
  fi
  stage_snapshot="$worktree/.pipeline/runs/$run_id/runtime/run-stage-$resume_stage.sh"
  cp "$script_dir/run-stage.sh" "$stage_snapshot"
  stage_args=(bash "$stage_snapshot" "$run_id" "$resume_stage"
    --worktree "$worktree" --change "$change" --codex-command "$codex_command")
  [ -n "$timeout" ] && stage_args+=(--timeout "$timeout")
  if ! PIPELINE_SCRIPT_DIR="$script_dir" "${stage_args[@]}"; then
    echo "stage failed: $resume_stage run_id=$run_id" >&2
    exit 1
  fi
done
