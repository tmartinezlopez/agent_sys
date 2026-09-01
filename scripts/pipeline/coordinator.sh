#!/usr/bin/env bash
# Entry point de la única sesión Codex coordinadora del proyecto.
set -euo pipefail

usage() {
  echo "uso: coordinator.sh [--worktree ruta] [--codex-command comando] [--timeout segundos]" >&2
  exit 1
}

worktree="${PIPELINE_REPO_ROOT:-$(pwd)}"
codex_command="codex"
timeout=""
while [ $# -gt 0 ]; do
  case "$1" in
    --worktree) worktree="${2:?--worktree requiere ruta}"; shift 2 ;;
    --codex-command) codex_command="${2:?--codex-command requiere comando}"; shift 2 ;;
    --timeout) timeout="${2:?--timeout requiere segundos}"; shift 2 ;;
    -h|--help) usage ;;
    *) usage ;;
  esac
done

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
worktree="$(cd "$worktree" && pwd)"
tmux_session="${PIPELINE_TMUX_SESSION:-$(basename "$worktree")-coordinator}"
export PIPELINE_REPO_ROOT="$worktree"
export PIPELINE_SCRIPT_DIR="$script_dir"
export PIPELINE_TMUX_SESSION="$tmux_session"

preflight_args=("$script_dir/preflight.sh" --worktree "$worktree")
[ "$(basename "$codex_command")" = codex ] && preflight_args+=(--real)
"${preflight_args[@]}" >/dev/null

guide="$script_dir/../../GUIA-USO.md"
[ -f "$guide" ] || { echo "FALTA guía de metodología: $guide" >&2; exit 1; }

prompt="Lee primero $guide. Eres el único coordinador principal de este proyecto.
Mantén la visión global, entiende el objetivo, planifica el trabajo, lanza y
controla las terminales/agentes necesarios, revisa sus resultados y decide los
gates y reintentos. Los roles del pipeline son subordinados y no coordinan ni
lanzan otros agentes. Para cada rol usa literalmente el launcher absoluto
 $script_dir/roles/launch-<rol>.sh; nunca reconstruyas una ruta relativa como
 metodologia/.... Los launchers disponibles son:
$script_dir/roles/ (launch-spec-writer.sh, launch-implementer.sh,
launch-test-runner.sh, launch-reviewer.sh, launch-ui-reviewer.sh,
launch-qa.sh). Cuando asignes una etapa, pásale --tmux y
--tmux-session "$tmux_session" para que cada rol tenga
una ventana visible e independiente. Usa siempre las herramientas desde la
 ruta absoluta $script_dir. Para preguntas sobre el backlog, usa primero
$script_dir/project-backlog.sh. Nunca uses $script_dir/../../docs/backlog.md
para responder sobre el proyecto: ese archivo sólo es el backlog interno de la
metodología. Si no existe un backlog del proyecto, dilo explícitamente. Cuando
el operador pida actualizar la metodología, ejecuta únicamente
 $script_dir/methodology-update.sh --project "$worktree". No ejecutes rsync
directamente ni inventes rutas de origen; si falta
 $worktree/metodologia/.config/source-path, detente y pide configurarlo una
sola vez. No hagas merge, push ni publicación automática. Si el run pertenece a un
worktree de feature, usa siempre ese worktree al consultar su ledger e informa
de la ruta exacta. Respeta siempre
\$PIPELINE_MAX_DISPATCHES y detente si falta una decisión humana."
command=("$codex_command" --dangerously-bypass-approvals-and-sandbox
  --model gpt-5.6-luna
  -c model_reasoning_effort=medium --cd "$worktree" --no-alt-screen "$prompt")
if [ -n "$timeout" ]; then
  timeout "$timeout" "${command[@]}"
else
  "${command[@]}"
fi
