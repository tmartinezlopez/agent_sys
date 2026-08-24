## Context

El runtime base ya ejecuta procesos Codex en tmux, persiste el ledger y conoce
el contrato de `spec-writer`. OpenSpec 1.10.0 está instalado en el checkout y
es la fuente de verdad para los artefactos de planificación.

## Goals / Non-Goals

**Goals:**

- Hacer que `spec-writer` produzca un change OpenSpec real.
- Separar el prompt del rol de la comprobación objetiva del coordinador.
- Dejar un handoff local que pueda consumir `implementer`.

**Non-Goals:**

- Implementar todavía `implementer` ni los otros roles.
- Añadir una API de OpenAI, un agente genérico o una segunda fuente de
  configuración.
- Aprobar automáticamente gates humanos posteriores.

## Decisions

- El coordinador preparará el nombre del change y el prompt contractual; Codex
  ejecutará el trabajo de redacción.
- El coordinador comprobará los artefactos y ejecutará la validación estricta.
  Así el resultado no depende únicamente de que Codex diga que terminó bien.
- El resultado contendrá rutas relativas al run y al change, además de la
  salida de validación. Se usará JSON para que el siguiente rol no dependa de
  texto libre.
- Se usará el CLI `openspec` local, no una librería Python nueva. Esto mantiene
  el mismo comportamiento que el operador ya puede verificar en terminal.

## Risks / Trade-offs

- [Risk] Codex puede crear un change incompleto → Mitigation: validación
  `--strict` y comprobación de los cuatro artefactos antes de `passed`.
- [Risk] Dos runs usan el mismo nombre → Mitigation: derivar el nombre del
  `run_id` o rechazar cambios existentes no pertenecientes al run.
- [Risk] El modelo deja texto ambiguo → Mitigation: prompt contractual y
  requisitos verificables en el change.
