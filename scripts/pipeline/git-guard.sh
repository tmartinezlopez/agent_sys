#!/usr/bin/env bash
# Git usado por procesos de agentes: integra localmente, pero nunca publica ni
# fusiona ramas desde el runtime.
set -euo pipefail

for argument in "$@"; do
  case "$argument" in
    merge|push)
      echo "runtime bloqueado: git $argument requiere una operación humana explícita" >&2
      exit 77
      ;;
  esac
done

real_git="${PIPELINE_REAL_GIT:-/usr/bin/git}"
[ -x "$real_git" ] || real_git="/bin/git"
exec "$real_git" "$@"
