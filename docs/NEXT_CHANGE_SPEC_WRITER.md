# Siguiente cambio: `spec-writer` real

El siguiente cambio implementará únicamente el rol `spec-writer` sobre el
runtime existente. No creará un agente genérico ni una configuración paralela.

## Entrada

- `run.json`: objetivo y `run_id`.
- `stages/spec-writer/prompt.md`: prompt contractual generado por el coordinador.
- Checkout Git del proyecto y configuración de OpenSpec.

## Trabajo del rol

1. Crear un change con `openspec new change "<nombre>"`.
2. Completar sus artefactos de planificación según el objetivo.
3. Comprobar el estado con `openspec status --change "<nombre>" --json`.
4. Validar con `openspec validate "<nombre>" --strict`.

El proceso se ejecutará con `gpt-5.6-luna`, reasoning `medium` y sandbox
`workspace-write`, tal como declara `src/agent_sys/contracts.py`.

## Salida obligatoria

El rol debe dejar un resumen final en la salida de Codex y el coordinador
registrará `stages/spec-writer/result.json`, junto con stdout, stderr y la
referencia al change OpenSpec creado. Si falta el change o la validación falla,
la etapa no supera `passed` y el pipeline se detiene.
