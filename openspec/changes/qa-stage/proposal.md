## Why

El pipeline ya puede especificar, implementar, probar y revisar un cambio, pero
todavía no tiene una etapa final que reúna esa evidencia y decida si el objetivo
completo está listo para entregarse. `qa` debe cerrar el flujo sin modificar el
checkout ni confiar en memoria implícita del proceso.

## What Changes

- Implementar la etapa real `qa` en solo lectura.
- Entregarle el objetivo original, los estados de las etapas anteriores y sus
  artefactos persistidos.
- Exigir una decisión estructurada `passed` o `blocked`, con hallazgos y
  evidencia.
- Persistir `qa-summary.json`, `result.json`, logs y el evento final de la etapa.
- Impedir que `qa` pase si falta una etapa obligatoria o si existe evidencia
  previa fallida/bloqueada.
- Verificar que `qa` no modifica el checkout.

## Capabilities

### New Capabilities

- `qa-stage`: validación final reproducible del objetivo y de la evidencia del
  pipeline.

### Modified Capabilities

- Ninguna.

## Impact

- Afecta a `src/agent_sys/pipeline.py` y añade el módulo de contrato/evaluación
  de `qa` si resulta necesario.
- Añade pruebas de handoff, decisión, evidencia incompleta, fallo del proceso y
  ausencia de mutaciones.
- Actualiza el backlog y la documentación del pipeline.
- No añade dependencias externas ni cambia el uso de `codex exec`.

