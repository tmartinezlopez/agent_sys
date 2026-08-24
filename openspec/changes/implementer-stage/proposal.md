## Why

El pipeline ya produce un change OpenSpec validado, pero todavía no tiene un
rol que convierta sus tareas en cambios reales del checkout. El `implementer`
es el siguiente paso necesario para que el sistema deje de detenerse después
de especificar.

## What Changes

- Implementar el contrato específico del rol `implementer`.
- Consumir exclusivamente el change OpenSpec producido por `spec-writer`.
- Ejecutar las tareas aprobadas en un checkout escribible y dejar evidencia.
- Comprobar que el change sigue siendo válido después de implementar.
- Detener el pipeline si falta el handoff, el checkout o la validación final.
- Mantener `gpt-5.4`, reasoning `medium` y sandbox `workspace-write`.

## Capabilities

### New Capabilities

- `implementer-stage`: Aplicación de tareas de un change OpenSpec validado y
  persistencia de la evidencia de implementación.

### Modified Capabilities

<!-- No se modifica el comportamiento del runtime general. -->

## Impact

- Afecta al prompt y a la evaluación del rol `implementer`.
- Permite modificaciones reales en el checkout; no crea todavía worktrees,
  gates humanos ni implementa los roles posteriores.
- Usa OpenSpec y Git locales, sin API de OpenAI.
