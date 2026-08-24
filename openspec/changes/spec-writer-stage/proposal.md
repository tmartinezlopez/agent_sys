## Why

El runtime ya puede ejecutar etapas, pero `spec-writer` todavía solo tiene un
contrato genérico. El siguiente paso debe producir un change OpenSpec real y
verificable para que el resto del pipeline trabaje sobre una especificación
concreta.

## What Changes

- Implementar el contrato de entrada y salida específico de `spec-writer`.
- Generar y validar changes OpenSpec desde el proceso externo de Codex.
- Registrar el nombre del change, sus artefactos y el resultado de validación.
- Detener la etapa si falta el change, un artefacto requerido o la validación.
- Mantener el modelo `gpt-5.6-luna`, reasoning `medium` y sandbox
  `workspace-write` ya declarados en el catálogo.

## Capabilities

### New Capabilities

- `spec-writer-stage`: Creación, validación y persistencia de la especificación
  producida por el primer rol del pipeline.

### Modified Capabilities

<!-- El contrato general del runtime no cambia en este change. -->

## Impact

- Afecta al prompt y a la evaluación de artefactos de `spec-writer`.
- Usa el CLI local de OpenSpec y el checkout Git actual.
- Añade pruebas de integración del contrato sin usar la API de OpenAI.
