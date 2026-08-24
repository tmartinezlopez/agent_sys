## Context

`spec-writer` ya deja un resultado estructurado con el nombre del change,
rutas de proposal, specs, design y tasks. El runtime tiene un rol
`implementer` escribible, pero todavía utiliza un prompt genérico y no valida
el handoff antes o después de ejecutar Codex.

## Goals / Non-Goals

**Goals:**

- Convertir el handoff de `spec-writer` en la entrada única de `implementer`.
- Mantener el trabajo dentro del checkout declarado y registrar evidencia.
- Validar la especificación después de implementar.

**Non-Goals:**

- Crear worktrees automáticos, commits o pushes desde el agente.
- Implementar tests, review, QA o gates humanos.
- Permitir que el agente cambie el contrato OpenSpec para ocultar errores.

## Decisions

- El coordinador leerá `spec-writer/result.json` y construirá el prompt con el
  nombre exacto del change y su `tasks.md`; no se volverá a inferir el objetivo
  desde texto libre.
- La comprobación de entrada exigirá que el change pertenezca al checkout y
  que sus artefactos existan antes de lanzar Codex.
- La comprobación de salida ejecutará `openspec validate --strict`; el éxito de
  Codex por sí solo no será suficiente.
- No se harán commits ni pushes automáticos: el operador conserva el control
  sobre GitHub.

## Risks / Trade-offs

- [Risk] Codex modifica archivos fuera del alcance → Mitigation: sandbox
  `workspace-write`, checkout explícito y registro de cambios posterior.
- [Risk] Las tareas del change quedan ambiguas → Mitigation: exigir el
  `tasks.md` del handoff y conservar el prompt completo.
- [Risk] Una validación estricta no detecta errores funcionales → Mitigation:
  dejar esa responsabilidad para `test-runner` y `reviewer`.
