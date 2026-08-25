## Why

El runtime ya ejecuta de forma real y auditable el tramo
`spec-writer → gate → implementer`, pero una feature termina demasiado pronto:
no hay ejecución coordinada de pruebas, revisión técnica, revisión UI
condicional ni QA antes de dejarla lista para integración humana.

## What Changes

- Extender la reanudación del run para despachar secuencialmente
  `test-runner`, `reviewer` y `qa` después de `implementer`.
- Añadir `ui-reviewer` únicamente para features marcadas explícitamente como
  afectadas por interfaz.
- Persistir prompts, comandos, resultados, fallos, reanudaciones y estado de
  cada nueva etapa en el mismo ledger y `run_id`.
- Hacer que un fallo o proceso interrumpido reanude la etapa abierta sin
  repetir etapas completadas.
- Abrir un gate final de revisión humana después de QA y mantener bloqueados
  merge, push y publicación automática.
- Ampliar status, health-check, logs, report y pruebas deterministas al flujo
  completo.

### No cambia en este bloque

- No se ejecutan merge, push, limpieza de worktrees ni publicación automática.
- No se incorpora un servicio persistente ni una UI de monitorización.
- No se añaden roles distintos de los seis ya declarados en el catálogo.

## Capabilities

### New Capabilities

Ninguna.

### Modified Capabilities

- `reference-codex-runtime`: completar el orden de etapas, la reanudación
  multi-etapa, la revisión UI condicional y el gate final de integración.

## Impact

- Modifica `scripts/pipeline/run-pipeline.sh`, `resume-run.sh`, el ledger y
  `stage-guard.py` para soportar etapas posteriores al implementer.
- Amplía contratos y evidencias en `scripts/pipeline/`, junto con los informes
  y comprobaciones operativas.
- Añade una opción explícita para indicar si una feature afecta a la UI.
- Requiere mantener disponibles los seis perfiles Codex declarados y sus
  sandboxes correspondientes.
