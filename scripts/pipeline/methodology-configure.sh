#!/usr/bin/env bash
set -euo pipefail
project="${PIPELINE_REPO_ROOT:-$(pwd)}"
source_dir=""
while [ $# -gt 0 ]; do
  case "$1" in
    --project) project="${2:?--project requiere ruta}"; shift 2 ;;
    --source) source_dir="${2:?--source requiere ruta}"; shift 2 ;;
    -h|--help) echo "uso: methodology-configure.sh --source ruta [--project ruta]"; exit 0 ;;
    *) echo "argumento desconocido: $1" >&2; exit 1 ;;
  esac
done
[ -n "$source_dir" ] || { echo "debes indicar --source una vez" >&2; exit 1; }
project="$(cd "$project" && pwd)"
source_dir="$(cd "$source_dir" && pwd)"
[ -f "$source_dir/roles.json" ] || { echo "origen inválido: falta roles.json" >&2; exit 1; }
mkdir -p "$project/metodologia/.config"
printf '%s\n' "$source_dir" > "$project/metodologia/.config/source-path"
printf 'METHODOLOGY_SOURCE_CONFIGURED=%s\n' "$source_dir"
