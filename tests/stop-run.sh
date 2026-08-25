#!/usr/bin/env bash
set -euo pipefail

root="$(cd "$(dirname "$0")/.." && pwd)"
tmp="$(mktemp -d /tmp/reference-codex-stop-XXXXXX)"
worktree="$tmp/feature-stop"
mkdir -p "$worktree/.pipeline/runs/run_stop"
python3 "$root/scripts/pipeline/run-ledger.py" init run_stop --worktree "$worktree" >/dev/null
printf '%s\n' '@7' > "$worktree/.pipeline/window-id"

fakebin="$tmp/bin"
mkdir -p "$fakebin"
cat > "$fakebin/tmux" <<'TMUX'
#!/usr/bin/env bash
set -euo pipefail
case "$1" in
  has-session) exit 0 ;;
  list-windows)
    case "$*" in
      *"#{window_id}"*) printf '@7\n@8\n' ;;
      *) printf '@7 pl:feature-stop\n@8 despacho\n' ;;
    esac
    ;;
  display-message)
    case "$*" in
      *"@8"*) printf 'despacho\n' ;;
      *) printf 'pl:feature-stop\n' ;;
    esac
    ;;
  kill-window) printf '%s\n' "$*" > "$TMUX_KILL_LOG"; exit 0 ;;
  *) exit 1 ;;
esac
TMUX
chmod +x "$fakebin/tmux"
kill_log="$tmp/kill.log"

before="$(sha256sum "$worktree/.pipeline/runs/run_stop/events.jsonl")"
PATH="$fakebin:$PATH" TMUX_KILL_LOG="$kill_log" \
  "$root/scripts/pipeline/stop-run.sh" run_stop --worktree "$worktree" --force >/dev/null
after="$(sha256sum "$worktree/.pipeline/runs/run_stop/events.jsonl")"
[ "$before" != "$after" ] || { echo "no registró la parada" >&2; exit 1; }
grep -q -- '-t @7' "$kill_log"
! grep -q -- '@8' "$kill_log"
python3 "$root/scripts/pipeline/run-logs.py" run_stop --worktree "$worktree" \
  | grep -q 'run_stopped'

printf '%s\n' '@8' > "$worktree/.pipeline/window-id"
if PATH="$fakebin:$PATH" TMUX_KILL_LOG="$kill_log" \
  "$root/scripts/pipeline/stop-run.sh" run_stop --worktree "$worktree" --force >/dev/null 2>&1; then
  echo "permitió parar la ventana protegida" >&2
  exit 1
fi
if grep -q -- '-t @8' "$kill_log"; then
  echo "mató la ventana despacho" >&2
  exit 1
fi

echo "stop-run safety: PASS"
