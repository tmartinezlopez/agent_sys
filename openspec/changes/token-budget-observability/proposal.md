## Why

El runtime limita el número de despachos, pero no ofrece un contador fiable de
tokens por etapa y run. Sin esa medida, el límite actual no permite controlar
coste ni detectar respuestas de Codex que no exponen uso.

## What Changes

- Extraer el uso de tokens cuando Codex CLI lo proporcione y normalizarlo por
  etapa y run.
- Registrar tokens de entrada, salida, razonamiento y caché cuando estén
  disponibles, distinguiendo siempre los valores desconocidos.
- Añadir presupuesto configurable por run y bloqueo antes del siguiente
  despacho cuando se supere.
- Exponer acumulados y motivo de bloqueo en estado, informe y diagnóstico.
- Mantener compatibilidad con ejecutores que no devuelvan métricas.

## Capabilities

### New Capabilities

- `token-budget-observability`: Medición y control de consumo del pipeline.

### Modified Capabilities

Ninguna. El presupuesto se introduce como un control opcional adicional.

## Impact

Afecta a `codex-run.py`, el ledger, `run-report.py`, `run-health-check.py` y la
configuración de límites. No cambia modelos ni requiere API externa.
