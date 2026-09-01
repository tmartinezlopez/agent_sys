# Flujo del pipeline

## Secuencia

```text
preflight → spec-writer → gate_spec → implementer → test-runner
          → reviewer → ui-reviewer (si aplica) → qa → gate_release
```

`new-feature.sh` crea la rama `feature/<item>`, el worktree y el `run_id` antes
de despachar el primer rol. Cada etapa conserva prompt, comando, resultado,
salida y error.

## Gates

- `gate_spec`: revisión humana de la especificación. `approve` permite seguir;
  `changes` deja el run reabrible; `discard` lo termina como descartado.
- `gate_release`: revisión final después de QA. Su aprobación deja la rama
  lista para integración humana.

Para continuar se reutiliza el mismo run:

```bash
scripts/pipeline/gate.sh RUN_ID approve operador --worktree "$PWD"
scripts/pipeline/resume-run.sh RUN_ID --worktree "$PWD"
```

## Ledger y recuperación

`.pipeline/runs/<run_id>/` contiene metadatos, eventos append-only, estado
derivado y evidencias. Las consultas reconstruyen el estado sin mutarlo.
`resume-run.sh` busca la primera etapa pendiente o abierta y no repite las ya
completadas.

## Operación

```bash
scripts/pipeline/pipelines-status.sh
python3 scripts/pipeline/run-health-check.py --worktree "$PWD"
python3 scripts/pipeline/run-report.py RUN_ID --worktree "$PWD"
scripts/pipeline/clean-runs.sh --worktree "$PWD" --older-than 604800
```

La primera limpieza sólo lista; `--force` es necesario para borrar runs
finalizados con `summary.json`.
