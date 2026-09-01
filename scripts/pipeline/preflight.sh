#!/usr/bin/env bash
# Comprueba requisitos sin crear worktrees, runs ni procesos Codex.
set -euo pipefail

worktree="${PIPELINE_REPO_ROOT:-$(pwd)}"
real=0
while [ $# -gt 0 ]; do
  case "$1" in
    --worktree) worktree="${2:?--worktree requiere ruta}"; shift 2 ;;
    --real) real=1; shift ;;
    *) echo "uso: preflight.sh [--worktree ruta] [--real]" >&2; exit 1 ;;
  esac
done
worktree="$(cd "$worktree" && pwd)"
fail=0
check_command() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "FALTA $1" >&2
    fail=1
  fi
}

[ -d "$worktree/.git" ] || [ -f "$worktree/.git" ] || { echo "NO_GIT $worktree" >&2; exit 1; }
check_command git
check_command python3
check_command openspec
[ -f "$worktree/openspec/config.yaml" ] || {
  echo "FALTA openspec/config.yaml en $worktree" >&2
  fail=1
}
script_dir="${PIPELINE_SCRIPT_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)}"
roles_file="${PIPELINE_ROLES_FILE:-$script_dir/roles.json}"
python3 - "$roles_file" <<'PY' || fail=1
import json
import sys
from pathlib import Path

path = Path(sys.argv[1])
roles = json.loads(path.read_text(encoding="utf-8"))
expected = {"spec-writer", "implementer", "test-runner", "reviewer", "ui-reviewer", "qa"}
if set(roles) != expected:
    raise SystemExit(f"roles inválidos: {sorted(roles)}")
for name, role in roles.items():
    if role.get("sandbox") not in {"workspace-write", "read-only"}:
        raise SystemExit(f"sandbox inválido para {name}")
print("roles: OK")
PY

if [ "$real" -eq 1 ]; then
  check_command codex
  [ "${PIPELINE_ALLOW_REAL_CODEX:-}" = 1 ] || {
    echo "Codex real requiere PIPELINE_ALLOW_REAL_CODEX=1" >&2
    fail=1
  }
  [ -n "${PIPELINE_MAX_DISPATCHES:-}" ] || {
    echo "Codex real requiere PIPELINE_MAX_DISPATCHES" >&2
    fail=1
  }
fi

if [ "$fail" -ne 0 ]; then
  echo "PREFLIGHT: FAIL" >&2
  exit 1
fi
printf 'PREFLIGHT: PASS worktree=%s real=%s\n' "$worktree" "$real"
