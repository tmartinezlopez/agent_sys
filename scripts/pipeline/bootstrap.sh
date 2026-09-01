#!/usr/bin/env bash
# Instala el runtime en un checkout consumidor sin tocar su configuración OpenSpec.
set -euo pipefail

target="${1:-}"
[ -n "$target" ] || {
  echo "uso: bootstrap.sh <proyecto> [--source ruta] [--force]" >&2
  exit 1
}
shift
source_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
force=0
while [ $# -gt 0 ]; do
  case "$1" in
    --source) source_dir="${2:?--source requiere ruta}"; shift 2 ;;
    --force) force=1; shift ;;
    *) echo "argumento desconocido: $1" >&2; exit 1 ;;
  esac
done
target="$(cd "$target" && pwd)"
source_dir="$(cd "$source_dir" && pwd)"
[ -d "$target/.git" ] || [ -f "$target/.git" ] || { echo "no es un checkout Git: $target" >&2; exit 1; }
[ -f "$source_dir/roles.json" ] || { echo "runtime inválido: falta roles.json" >&2; exit 1; }
destination="$target/scripts/pipeline"
if [ -e "$destination" ] && [ "$force" -ne 1 ]; then
  echo "ya existe $destination; usa --force para actualizar sólo el runtime" >&2
  exit 1
fi
mkdir -p "$destination"
cp -R "$source_dir"/. "$destination"/
find "$destination" -type d -name __pycache__ -prune -exec rm -rf {} +
find "$destination" -type f \( -name '*.sh' -o -name '*.py' \) -exec chmod +x {} +
mkdir -p "$target/metodologia/.config"
printf '%s\n' "$(cd "$source_dir/../.." && pwd)" > "$target/metodologia/.config/source-path"
printf '%s\n' "runtime instalado en $destination"
printf '%s\n' "siguiente: $destination/preflight.sh --worktree $target"
