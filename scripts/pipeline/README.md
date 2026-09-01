# Runtime del pipeline

Esta carpeta contiene la mecánica operativa del sistema: worktrees, ledger,
despacho Codex, gates, reanudación, consultas y parada segura. Los contratos de
los roles se mantienen separados de esta capa.

El coordinador es el Codex principal del proyecto y conserva la visión global.
Es quien decide el desglose, lanza/controla terminales y agentes, supervisa
las etapas y toma las decisiones. Los roles del catálogo son trabajadores
especializados por etapa; no son coordinadores ni deben lanzar otros agentes.

El punto de entrada de esa sesión es `coordinator.sh`. Usa el Codex
interactivo y permanece abierto. El coordinador y los agentes se lanzan con
`--dangerously-bypass-approvals-and-sandbox`, por lo que el operador debe
ejecutarlos sólo en un checkout aislado y bajo su responsabilidad.

Para crear siempre un coordinador nuevo, sin reutilizar una sesión anterior:

```bash
coordinator-start.sh --worktree /ruta/proyecto
tmux attach-session -t NOMBRE_DEVUELTO
```

`coordinator-start.sh` crea y registra una sesión nueva y, en un entorno
gráfico, abre automáticamente una terminal visible conectada a ella. Usa
`--detach` para no abrirla, o `--no-open-terminal` para conectar la terminal
actual cuando exista un TTY.

Para cerrar uno concreto:

```bash
coordinator-stop.sh --session NOMBRE_DEVUELTO
```

Cada arranque usa un proceso Codex interactivo y un nombre de sesión único; no
usa `codex resume` ni hereda el contexto conversacional de otro coordinador.

La sesión se configura como una terminal normal: historial de 10.000 líneas,
scroll con rueda, selección con ratón y copia al portapapeles. Para configurar
una sesión antigua sin reiniciarla:

```bash
tmux-setup.sh --session NOMBRE_SESION
```

También se puede entrar en scroll manual con `Ctrl-b` y `[`, salir con `q` y
moverse con las flechas o PageUp/PageDown.

Cada rol tiene además un launcher explícito en `roles/`:
`launch-spec-writer.sh`, `launch-implementer.sh`, `launch-test-runner.sh`,
`launch-reviewer.sh`, `launch-ui-reviewer.sh` y `launch-qa.sh`. El coordinador
elige y ejecuta estos launchers; no se crean coordinadores por tarea.
Para que el operador pueda inspeccionar el trabajo, el coordinador debe
invocarlos con `--tmux --tmux-session <sesión>`; cada rol se abre en su propia
ventana, titulada `ROLE:<rol>`. El panel también recibe ese título. La ventana
se cierra automáticamente cuando termina el proceso del rol; no se dejan
shells huérfanas abiertas.

`project-backlog.sh` localiza el backlog del checkout consumidor y excluye
deliberadamente `metodologia/docs/backlog.md`, que pertenece al runtime.
Los launchers deben invocarse siempre mediante su ruta absoluta
`$PIPELINE_SCRIPT_DIR/roles/launch-<rol>.sh`; no se permite resolverlos desde
el `PWD` del agente.
Para actualizar la metodología se usa exclusivamente
`methodology-update.sh`; los agentes no deben ejecutar `rsync` directamente ni
inventar rutas de la copia maestra.

## Flujo principal

- new-feature.sh <item> <objetivo> [--ui] crea feature/<item> en un worktree y
  lanza el slice spec-writer. `--ui` incluye `ui-reviewer` en las etapas
  posteriores.
- gate.sh <run_id> approve|changes|discard <operator> [reason] --worktree
  <ruta> registra la decisión humana. Para el gate final se añade
  `--gate gate_release`.
- resume-run.sh <run_id> --worktree <ruta> continúa el mismo run desde la
  primera etapa abierta y avanza por `implementer`, `test-runner`, `reviewer`,
  `ui-reviewer` (si aplica) y `qa`.
- stop-run.sh <run_id> --worktree <ruta> --force detiene sólo la ventana tmux
  registrada para ese run y deja el worktree intacto.

Cada run queda en `.pipeline/runs/<run_id>/` con `run.json`, `events.jsonl`,
estado derivado, `summary.json` y evidencias por etapa. Tras QA se abre
`gate_release`; sólo su aprobación deja el run en `completed`. Una decisión
`changes` deja el gate reabrible para una aprobación posterior; `discard` deja
el run terminal en `discarded`. Ese estado es local y está ignorado por Git.

Antes de crear un worktree se ejecuta `preflight.sh`. Para instalar este
runtime en otro checkout se puede usar `bootstrap.sh <proyecto> --source
<ruta-a-scripts/pipeline>` y después repetir el preflight.

El Codex real está bloqueado por defecto. Para una ejecución manual explícita
se requieren `PIPELINE_ALLOW_REAL_CODEX=1` y `PIPELINE_MAX_DISPATCHES=<límite>`;
por ejemplo, `PIPELINE_MAX_DISPATCHES=1` permite validar sólo el primer agente.
Las pruebas del repositorio usan un ejecutor falso y no consumen cuota.

Los runs terminados se pueden listar y limpiar con
`clean-runs.sh --worktree <ruta> --older-than <segundos>`; la eliminación exige
añadir `--force` y nunca afecta runs sin `summary.json`.

Un proyecto puede proporcionar su propio catálogo validado con
`PIPELINE_ROLES_FILE=/ruta/roles.json`. El catálogo debe conservar exactamente
los seis roles y los sandboxes esperados.

Compatibilidad de referencia: Git 2.x, Bash 4+, Python 3.11+, OpenSpec 1.10+,
Codex CLI 0.150.1 y tmux 3.6 (tmux es opcional si se usa `--no-tmux`).

## Consultas

- pipelines-status.sh lista los runs del checkout y sus worktrees, etapas
  completadas y gates pendientes.
- run-health-check.py devuelve triage JSON read-only, incluidos gates y
  posibles estancamientos.
- run-logs.py <run_id> muestra eventos, prompts y stdout/stderr persistidos.
- run-report.py <run_id> resume etapas, modelos, sandbox y resultados Codex.

Las consultas leen el ledger en memoria: no regeneran `current-state.json`, no
añaden eventos y no crean `summary.json`.

## Seguridad

codex-run.py ejecuta sólo roles declarados en roles.json y antepone
git-guard.sh al PATH del proceso agente. El wrapper rechaza git merge y
git push; la integración de la rama queda para una revisión humana posterior.

Las funciones de lib-paths.sh son la única fuente de verdad para nombres de
worktrees, ramas, ventanas y runs. Los scripts no hacen merge ni push por sí
mismos.

## Consumo responsable

Las pruebas del runtime deben usar un Codex falso determinista. Una E2E con el
Codex real es una operación manual y excepcional, no parte de cada cambio.

La reanudación reutiliza el `run_id` y no vuelve a despachar etapas completadas.
El runtime todavía no implementa una caché explícita de prompts ni un contador
de tokens; esa capacidad queda pendiente antes de habilitar ejecuciones reales
frecuentes. No se debe interpretar el almacenamiento de logs como caché de
contexto del modelo.
