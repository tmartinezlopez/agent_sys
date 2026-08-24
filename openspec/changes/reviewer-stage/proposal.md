## Why

Después de implementar y probar, el pipeline necesita una revisión independiente
que detecte problemas de contrato, seguridad, calidad y evidencia antes de QA.

## What Changes

- Implementar `reviewer` como etapa read-only.
- Consumir los handoffs de implementer y test-runner.
- Revisar diff, tareas, tests y validación OpenSpec.
- Producir un informe estructurado con hallazgos y decisión.
- Bloquear el pipeline ante hallazgos críticos o evidencia insuficiente.
- Mantener `gpt-5.6-luna`, reasoning `medium` y sandbox `read-only`.

## Capabilities

### New Capabilities

- `reviewer-stage`: Revisión independiente y auditable de una implementación
  probada.

### Modified Capabilities

<!-- No se modifica el contrato general del runtime. -->

## Impact

- Afecta al prompt y a la evaluación de `reviewer`.
- No modifica el checkout ni crea commits o pushes.
- Añade evidencia para las etapas posteriores.
