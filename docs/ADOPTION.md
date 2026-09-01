# Adopción en otro proyecto

## Requisitos

- Checkout Git con una rama base disponible.
- Bash 4+, Python 3.11+, Git 2.x y OpenSpec 1.10+.
- Codex CLI 0.150.1 autenticado sólo cuando se vaya a ejecutar un agente real.
- tmux 3.6 es opcional; usar `--no-tmux` sin él.

## Instalación

Desde este repositorio:

```bash
scripts/pipeline/bootstrap.sh /ruta/proyecto \
  --source /ruta/agent_sys/scripts/pipeline
```

El bootstrap sólo copia los archivos del runtime. No reemplaza
`openspec/config.yaml` ni las especificaciones del proyecto. Ejecutar después:

```bash
/ruta/proyecto/scripts/pipeline/preflight.sh --worktree /ruta/proyecto
```

Añadir al `.gitignore` del consumidor:

```gitignore
.pipeline/*
!.pipeline/toolchain/
!.pipeline/toolchain/**
```

## Ejecución segura

Las pruebas deterministas usan un comando falso. Para Codex real hay que
activar ambos límites explícitamente:

```bash
cd /ruta/proyecto
PIPELINE_ALLOW_REAL_CODEX=1 \
PIPELINE_MAX_DISPATCHES=1 \
scripts/pipeline/new-feature.sh mi-feature \
  "objetivo de la funcionalidad" --codex-command codex --no-tmux
```

El valor `1` sirve para validar sólo `spec-writer`. Para un flujo no-UI completo
se necesita un límite de `5`. El límite cuenta reintentos y no se restablece al
reanudar. La revisión UI de la v1 se valida de forma determinista; no se
requiere ni se ejecuta una E2E UI real.

El comando termina en `gate_spec`. Tras revisar el change:

```bash
scripts/pipeline/gate.sh RUN_ID approve operador --worktree WORKTREE
scripts/pipeline/resume-run.sh RUN_ID --worktree WORKTREE
```

Después de QA se abre `gate_release`. Sólo su aprobación permite cerrar el run.
`changes` registra que el operador debe corregir y volver a aprobar; `discard`
termina el run como descartado. Ninguna operación hace merge, push o limpieza
automática.

## Diagnóstico y limpieza

```bash
scripts/pipeline/pipelines-status.sh
python3 scripts/pipeline/run-health-check.py --worktree WORKTREE
python3 scripts/pipeline/run-report.py RUN_ID --worktree WORKTREE
scripts/pipeline/clean-runs.sh --worktree WORKTREE --older-than 604800
scripts/pipeline/clean-runs.sh --worktree WORKTREE --older-than 604800 --force
```

La primera orden de limpieza sólo lista. `--force` elimina exclusivamente runs
con `summary.json` que superen la antigüedad indicada.
