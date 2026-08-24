## Context

El pipeline ya tiene handoffs persistentes de `implementer` y `test-runner`.
`reviewer` está declarado como read-only, pero todavía solo dispone del prompt
genérico de la etapa.

## Goals / Non-Goals

**Goals:**

- Revisar de forma independiente el diff y la evidencia producida.
- Dejar un resultado estructurado consumible por QA.
- Impedir mutaciones del checkout.

**Non-Goals:**

- Corregir código automáticamente.
- Ejecutar UI review o QA.
- Aprobar pushes o commits.

## Decisions

- El coordinador exigirá los estados pasados de implementer y test-runner antes
  de lanzar reviewer.
- El agente recibirá rutas explícitas a resultados, change, tareas y logs.
- El resultado deberá contener decisión y hallazgos; el coordinador comprobará
  la estructura mínima y el estado Git antes de aceptar `passed`.
- El sandbox y las verificaciones de Git permanecerán read-only.

## Risks / Trade-offs

- [Risk] El modelo puede omitir un problema → Mitigation: prompt con checklist
  y evidencia obligatoria; QA hará la comprobación final.
- [Risk] El agente intenta editar → Mitigation: sandbox read-only y comparar
  estado Git antes y después.
