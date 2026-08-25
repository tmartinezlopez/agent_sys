#!/usr/bin/env bash
# Detiene únicamente la ventana tmux registrada para un run.
set -eo pipefail

run_id="$1"
[ -n "$run_id" ] || {
  echo "uso: stop-run.sh <run_id> --worktree ruta [--force]" >&2
  exit 2
}
shift
worktree=""
force=0
while [ $# -gt 0 ]; do
  case "$1" in
    --worktree)
      worktree="$2"
      [ -n "$worktree" ] || { echo "--worktree requiere ruta" >&2; exit 2; }
      shift 2
      ;;
    --force) force=1; shift ;;
    *) echo "argumento desconocido: $1" >&2; exit 2 ;;
  esac
done

script_dir="$(cd "$(dirname "$0")" && pwd)"
# shellcheck source=lib-paths.sh
source "$script_dir/lib-paths.sh"

if [ -z "$worktree" ]; then
  worktree="$(pl_find_run_worktree "$run_id" || true)"
fi
[ -n "$worktree" ] || { echo "no se pudo localizar el worktree de $run_id" >&2; exit 1; }
worktree="$(cd "$worktree" && pwd)"
run_dir="$worktree/.pipeline/runs/$run_id"
[ -d "$run_dir" ] || { echo "run no encontrado: $run_id" >&2; exit 1; }

record() {
  status="$1"
  target="$2"
  detail="$3"
  python3 "$script_dir/run-ledger.py" event "$run_id" run_stopped \
    --emitter human --worktree "$worktree" --payload \
    "$(python3 - "$status" "$target" "$detail" <<'PY'
import json
import sys
status, target, detail = sys.argv[1:]
print(json.dumps({"stopStatus": status, "target": target, "detail": detail or None}))
PY
)" >/dev/null
}

item="$(basename "$worktree")"
window="pl:$item"
session="$repo_name"
id_file="$worktree/.pipeline/window-id"
target=""
resolved_by=""

if ! command -v tmux >/dev/null 2>&1; then
  record unavailable "" "tmux no disponible"
  echo "tmux no está disponible; no se ha matado ningún proceso." >&2
  exit 1
fi
if ! tmux has-session -t "=$session" 2>/dev/null; then
  record not_running "" "sesión tmux ausente"
  echo "no hay sesión tmux '$session'; no hay nada que parar"
  exit 0
fi

if [ -r "$id_file" ]; then
  window_id="$(sed -n '1p' "$id_file")"
  if [ -n "$window_id" ] && tmux list-windows -t "=$session" -F '#{window_id}' 2>/dev/null \
      | grep -qxF "$window_id"; then
    target="$window_id"
    resolved_by="id registrado"
  fi
fi
if [ -z "$target" ]; then
  target="$(tmux list-windows -t "=$session" -F '#{window_id} #{window_name}' 2>/dev/null \
    | awk -v wanted="$window" '$2 == wanted {print $1; exit}')"
  [ -n "$target" ] && resolved_by="nombre exacto"
fi
if [ -z "$target" ]; then
  record not_running "" "ventana $window ausente"
  echo "no hay ventana '$window'; no hay nada que parar"
  exit 0
fi

target_name="$(tmux display-message -p -t "$target" '#{window_name}' 2>/dev/null || true)"
if [ "$target_name" = "despacho" ]; then
  record refused "$target" "la ventana despacho está protegida"
  echo "ABORTADO: nunca se detiene la ventana despacho" >&2
  exit 1
fi
if [ "$force" -ne 1 ]; then
  record refused "$target" "requiere --force"
  echo "objetivo resuelto: $target [$target_name] ($resolved_by); repite con --force" >&2
  exit 1
fi

if tmux kill-window -t "$target"; then
  record stopped "$target" "$target_name"
  echo "run=$run_id detenido; worktree intacto: $worktree"
else
  record failed "$target" "tmux kill-window falló"
  echo "no se pudo detener la ventana $target" >&2
  exit 1
fi
