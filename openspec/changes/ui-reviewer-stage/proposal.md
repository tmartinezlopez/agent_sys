## Why

La referencia incluye una revisión visual real para cambios de frontend, pero
nuestro Codex no tiene actualmente ningún MCP o bridge de navegador configurado.
Necesitamos formalizar una etapa condicional que revise UI cuando exista una
capacidad real y que marque `NO_VERIFICABLE` cuando no exista, sin fingir
capturas ni resultados visuales.

## What Changes

- Implementar el contrato condicional de `ui-reviewer`.
- Detectar si el change afecta a frontend mediante el diff y los artefactos.
- Exigir una capacidad de navegador real y un servidor de desarrollo accesible.
- Persistir rutas, escenarios, capturas/evidencias y veredicto.
- Devolver `NO_VERIFICABLE`/`blocked` si falta navegador o servidor.
- Mantener `gpt-5.4`, reasoning `medium` y sandbox `read-only`.

## Capabilities

### New Capabilities

- `ui-reviewer-stage`: Revisión visual condicional con evidencia real o bloqueo
  explícito por falta de capacidad.

### Modified Capabilities

<!-- No se modifica el contrato general del runtime. -->

## Impact

- Afecta al prompt y evaluación de `ui-reviewer`.
- Requerirá una integración MCP/browser real antes de poder pasar una revisión
  visual en producción.
- No añadirá un navegador simulado ni una implementación falsa.
