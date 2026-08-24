## Why

El pipeline ya puede especificar e implementar, pero todavía no tiene una
etapa que ejecute las pruebas de forma independiente y deje evidencia objetiva
antes de revisar el código.

## What Changes

- Implementar el contrato real de `test-runner` en solo lectura.
- Consumir el resultado pasado de `implementer` y su checkout.
- Ejecutar las pruebas declaradas por el proyecto.
- Persistir comandos, salida, código de salida y resumen de fallos.
- Bloquear el pipeline si no existe un handoff válido o las pruebas fallan.
- Mantener `gpt-5.3-codex`, reasoning `medium` y sandbox `read-only`.

## Capabilities

### New Capabilities

- `test-runner-stage`: Ejecución reproducible y observable de pruebas sobre la
  implementación producida por el pipeline.

### Modified Capabilities

<!-- No se modifica el contrato general del runtime. -->

## Impact

- Afecta al prompt y a la evaluación de `test-runner`.
- Añade evidencia de pruebas al run, sin modificar el checkout.
- Usa las herramientas de prueba ya declaradas por el proyecto; no añade API
  de OpenAI ni dependencias externas.
