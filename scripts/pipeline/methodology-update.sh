#!/usr/bin/env bash
set -euo pipefail
project="${PIPELINE_REPO_ROOT:-$(pwd)}"
while [ $# -gt 0 ]; do
  case "$1" in
    --project) project="${2:?--project requiere ruta}"; shift 2 ;;
    -h|--help) echo "uso: methodology-update.sh [--project ruta]"; exit 0 ;;
    *) echo "argumento desconocido: $1" >&2; exit 1 ;;
  esac
done
project="$(cd "$project" && pwd)"
config="$project/metodologia/.config/source-path"
[ -f "$config" ] || { echo "falta $config; configura el origen una vez" >&2; exit 1; }
source_dir="$(<"$config")"
[ -d "$source_dir" ] || { echo "origen no disponible: $source_dir" >&2; exit 1; }
rsync -a --delete \
  --exclude .git --exclude .pipeline --exclude .pytest_cache \
  --exclude '__pycache__' --exclude '.config' \
  "$source_dir/" "$project/metodologia/"
mkdir -p "$project/metodologia/.config"
printf '%s\n' "$source_dir" > "$project/metodologia/.config/source-path"
find "$project/metodologia/scripts" -type f \( -name '*.sh' -o -name '*.py' \) \
  -exec chmod +x {} +
printf 'METHODOLOGY_UPDATED source=%s\n' "$source_dir"
