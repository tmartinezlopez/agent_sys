#!/usr/bin/env bash
# Configura una sesión tmux para uso normal de terminal y scroll.
set -euo pipefail

session=""
while [ $# -gt 0 ]; do
  case "$1" in
    --session) session="${2:?--session requiere nombre}"; shift 2 ;;
    -h|--help) echo "uso: tmux-setup.sh --session nombre"; exit 0 ;;
    *) echo "argumento desconocido: $1" >&2; exit 1 ;;
  esac
done
[ -n "$session" ] || { echo "debes indicar --session explícitamente" >&2; exit 1; }
tmux has-session -t "$session" 2>/dev/null || {
  echo "sesión tmux inexistente: $session" >&2
  exit 1
}

tmux set-option -t "$session" history-limit 10000
tmux set-option -t "$session" mouse on
tmux set-option -t "$session" escape-time 0
tmux set-option -t "$session" focus-events on
tmux set-option -t "$session" set-clipboard on
tmux set-window-option -t "$session" mode-keys emacs
tmux set-window-option -t "$session" allow-passthrough off
# Fuerza el comportamiento de scroll aunque la terminal o la aplicación
# intenten capturar los eventos de rueda. La primera rueda entra en historial;
# las siguientes suben o bajan dentro de copy-mode.
tmux bind-key -T root WheelUpPane \
  if-shell -F '#{pane_in_mode}' 'send-keys -M' \
  'copy-mode -e \; send-keys -X scroll-up'
tmux bind-key -T root WheelDownPane \
  if-shell -F '#{pane_in_mode}' 'send-keys -M' \
  'send-keys -M'
tmux bind-key -T copy-mode WheelUpPane send-keys -X scroll-up
tmux bind-key -T copy-mode WheelDownPane send-keys -X scroll-down
tmux bind-key -T copy-mode-vi WheelUpPane send-keys -X scroll-up
tmux bind-key -T copy-mode-vi WheelDownPane send-keys -X scroll-down
printf 'TMUX_CONFIGURED session=%s history=10000 mouse=on\n' "$session"
