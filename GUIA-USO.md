# Guía de uso de la metodología

Documentos relacionados: [arquitectura](docs/ARCHITECTURE.md),
[flujo del pipeline](docs/PIPELINE.md), [adopción](docs/ADOPTION.md),
[actualización](docs/UPDATING.md) y [contrato del proyecto](docs/PROJECT-CONTRACT.md).

Esta carpeta se copia dentro de cada proyecto con el nombre `metodologia/`.
No se instala como una aplicación ni se mezcla con el código del proyecto.

La ruta de la copia maestra se registra una sola vez en
`metodologia/.config/source-path`. No se escribe en los prompts ni se repite
en los comandos del coordinador.

## Jerarquía de trabajo

El coordinador es el Codex principal del proyecto. Es una única instancia con
visión global: entiende el objetivo, divide el trabajo, lanza y controla las
terminales/agentes, revisa sus resultados, decide cuándo avanzar y mantiene el
estado general del proyecto.

Los roles `spec-writer`, `implementer`, `test-runner`, `reviewer`,
`ui-reviewer` y `qa` son agentes subordinados especializados. Cada uno
resuelve una etapa concreta que el coordinador le asigna; ninguno coordina el
proyecto ni lanza otros agentes.

Los scripts de `metodologia/scripts/pipeline/` son herramientas que utiliza el
coordinador para preparar worktrees, despachar una etapa, consultar el estado
y reanudar una ejecución. No son un coordinador adicional.

Cada agente tiene un launcher propio en
`metodologia/scripts/pipeline/roles/`. El coordinador usa esos launchers para
abrir una ventana tmux independiente para cada rol; debe pasar `--tmux` y
`--tmux-session "$(basename "$PWD")-coordinator"`. No llama a un agente
genérico ni mezcla roles.

El backlog de `metodologia/docs/backlog.md` sólo describe mejoras de esta
metodología. No es el backlog del proyecto consumidor. Para consultar el
backlog del proyecto, el coordinador debe usar:

```bash
metodologia/scripts/pipeline/project-backlog.sh --worktree "$PWD"
```

También reconoce `TASKS.md`, `tasks.md` y documentos de `docs/` cuyo nombre
contenga `backlog` o `tasks`. Si no encuentra un backlog del proyecto, debe
decirlo explícitamente.

## 1. Primera configuración

Desde la raíz del proyecto:

```bash
cp -R /ruta/agent_sys ./metodologia
```

Registra el origen una sola vez:

```bash
metodologia/scripts/pipeline/methodology-configure.sh \
  --project "$PWD" --source /ruta/agent_sys
```

El proyecto debe tener Git, una rama base confirmada (`main` o `master`) y
`openspec/config.yaml`. Comprueba la instalación:

```bash
PIPELINE_REPO_ROOT="$PWD" \
PIPELINE_SCRIPT_DIR="$PWD/metodologia/scripts/pipeline" \
metodologia/scripts/pipeline/preflight.sh --worktree "$PWD"
```

Añade al `.gitignore`:

```gitignore
.pipeline/*
```

Haz un commit del proyecto y de `metodologia/` antes de usarla.

El punto de entrada siempre es el coordinador. No se lanza `new-feature.sh`
directamente salvo para una comprobación técnica del runtime.

Para arrancarlo correctamente en una sesión nueva y visible:

```bash
PIPELINE_ALLOW_REAL_CODEX=1 \
PIPELINE_MAX_DISPATCHES=5 \
metodologia/scripts/pipeline/coordinator-start.sh --worktree "$PWD"
```

El comando crea y muestra automáticamente una terminal gráfica conectada a la
sesión. Si se lanza con `--detach`, devuelve el nombre exacto y puedes entrar con
`tmux attach-session -t NOMBRE_DEVUELTO`. Cada ejecución crea un coordinador
nuevo y no reutiliza el contexto de otro.

La sesión se crea con ratón y scroll activados y con historial ampliado. Para
desplazarte manualmente en tmux usa `Ctrl-b` y después `[`. Para salir del modo
de desplazamiento pulsa `q`.

El coordinador aparece como `COORDINATOR`. Cada agente aparece en una ventana
`ROLE:<rol>` y se cierra automáticamente al terminar su tarea. Mientras está
activo puedes cambiar de ventana con `Ctrl-b` y las flechas, o haciendo clic
en el título de la ventana.

Si ya existe una sesión antigua, se puede aplicar la misma configuración sin
reiniciarla:

```bash
metodologia/scripts/pipeline/tmux-setup.sh \
  --session NOMBRE_DE_LA_SESION
```

Para cerrar el coordinador al terminar:

```bash
metodologia/scripts/pipeline/coordinator-stop.sh \
  --session NOMBRE_DEVUELTO
```

## Actualizar una metodología ya instalada

Cuando se hagan cambios en la copia maestra, desde la raíz de cada proyecto
consumidor ejecuta:

```bash
metodologia/scripts/pipeline/methodology-update.sh --project "$PWD"
```

Este script es obligatorio. No actualices `metodologia/` ejecutando `rsync`
directamente ni escribiendo una ruta de origen en el prompt. Si falta
`metodologia/.config/source-path`, ejecuta primero
`methodology-configure.sh` una sola vez con la ruta que indique el operador.

Después valida la copia y registra la actualización en Git:

```bash
PIPELINE_REPO_ROOT="$PWD" \
PIPELINE_SCRIPT_DIR="$PWD/metodologia/scripts/pipeline" \
metodologia/scripts/pipeline/preflight.sh --worktree "$PWD"
git add metodologia
git commit -m "Actualiza la metodología"
```

## 2. Primera ejecución: validación barata

Valida primero el circuito sin consumir Codex real:

```bash
bash metodologia/tests/check-all.sh
```

Después arranca el coordinador interactivo sin pasarle ninguna tarea. La
terminal queda abierta y el operador le da las instrucciones directamente:

```bash
PIPELINE_REPO_ROOT="$PWD" \
PIPELINE_SCRIPT_DIR="$PWD/metodologia/scripts/pipeline" \
PIPELINE_ALLOW_REAL_CODEX=1 \
PIPELINE_MAX_DISPATCHES=1 \
metodologia/scripts/pipeline/coordinator.sh \
  --worktree "$PWD" \
  --codex-command codex
```

Este límite valida sólo la generación de la especificación. Revisa el
resultado y aprueba el gate:

```bash
metodologia/scripts/pipeline/gate.sh RUN_ID approve operador \
  --worktree "$PWD"
metodologia/scripts/pipeline/resume-run.sh RUN_ID --worktree "$PWD"
```

`RUN_ID` es el identificador mostrado por el comando. Usa `changes` si hay que
corregir algo y `discard` si se descarta la funcionalidad.

## 3. Uso normal

Para cada nueva funcionalidad se continúa la sesión del coordinador. El
coordinador es quien decide cuándo usar `new-feature.sh`:

```bash
PIPELINE_REPO_ROOT="$PWD" \
PIPELINE_SCRIPT_DIR="$PWD/metodologia/scripts/pipeline" \
PIPELINE_ALLOW_REAL_CODEX=1 \
PIPELINE_MAX_DISPATCHES=5 \
metodologia/scripts/pipeline/coordinator.sh \
  --worktree "$PWD" \
  --codex-command codex
```

El flujo se detiene en los gates humanos. El operador revisa, aprueba y
reanuda el mismo `RUN_ID`; no vuelve a lanzar `new-feature.sh` para continuar
una ejecución pausada.

Todas las órdenes del coordinador deben usar la ruta absoluta contenida en
`PIPELINE_SCRIPT_DIR`. No debe reconstruir rutas como `metodologia/...` desde
el directorio actual, porque una feature puede ejecutarse desde otro
worktree.

Con Codex real, cada etapa se abre automáticamente en una ventana tmux de la
sesión del coordinador. El pipeline espera su resultado en el ledger antes de
abrir la siguiente; no depende de que Codex recuerde añadir `--tmux`.

El límite `5` corresponde al flujo no-UI completo, cuenta reintentos y no se
reinicia al reanudar. La E2E UI real queda fuera de esta versión; la cobertura
UI determinista sí está incluida.

## 4. Consultar y limpiar

```bash
metodologia/scripts/pipeline/pipelines-status.sh
python3 metodologia/scripts/pipeline/run-health-check.py --worktree "$PWD"
python3 metodologia/scripts/pipeline/run-report.py RUN_ID --worktree "$PWD"
```

Para listar y después limpiar ejecuciones antiguas:

```bash
metodologia/scripts/pipeline/clean-runs.sh --worktree "$PWD" --older-than 604800
metodologia/scripts/pipeline/clean-runs.sh --worktree "$PWD" --older-than 604800 --force
```

Las ejecuciones viven en `.pipeline/runs/` y no forman parte del código
funcional.

## Regla de trabajo

Las pruebas normales usan un agente falso y no consumen cuota. Codex real se
lanza sólo para implementar una funcionalidad, siempre con límite explícito y
revisión humana. La reanudación reutiliza el `RUN_ID` y no repite etapas
completadas.

La caché de resultados read-only está desactivada por defecto. Sólo se activa
de forma explícita con `PIPELINE_PROMPT_CACHE_MODE=read-write`; sus decisiones
quedan en `result.json`, `run-report.py` y `run-logs.py`. No cachea roles que
escriben en el checkout.

El contador de tokens se activa con `PIPELINE_MAX_TOKENS=<entero>`. El runtime
registra el uso conocido por etapa y run; las métricas que Codex no proporcione
quedan como `unknown`.
