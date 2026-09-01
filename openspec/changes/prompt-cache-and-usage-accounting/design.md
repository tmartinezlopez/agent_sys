## Context

El runtime usa `codex exec` y conserva evidencia bajo `.pipeline/runs`.
Actualmente esa evidencia no es una caché reutilizable. Véase `proposal.md` y
el contrato de `reference-codex-runtime`.

## Goals / Non-Goals

**Goals:** reducir repeticiones controlables, hacer la decisión auditable y
evitar contaminación entre proyectos, roles o configuraciones.

**Non-Goals:** cachear respuestas parciales, compartir datos entre proyectos,
ocultar una llamada real al operador o sustituir la reanudación basada en el
ledger.

## Decisions

- Usar una clave hash derivada de prompt, versión del contrato, rol, modelo,
  razonamiento y configuración del proyecto; no usar texto del prompt como
  nombre de archivo. Así se evita colisión y exposición accidental.
- Mantener la caché fuera del ledger y enlazar desde la evidencia de etapa.
  El ledger seguirá siendo la fuente de estado, mientras la caché es una
  optimización prescindible.
- Limitar la reutilización a resultados exitosos de roles `read-only` y exigir
  una huella del checkout. Los roles con escritura no se cachean porque un
  resultado anterior no demuestra que sus cambios sigan presentes.
- Activarla mediante configuración explícita y permitir `off`, `read-only` y
  `read-write`. La alternativa de activarla siempre se descarta por riesgo de
  reutilizar contexto obsoleto.
- Validar tamaño, permisos y versión de formato antes de leer; ante cualquier
  error se ejecuta Codex normalmente y se registra el bypass.

## Risks / Trade-offs

- [Contexto obsoleto] → incluir versión de contrato, configuración y huella del
  checkout en la clave, además de permitir invalidación manual.
- [Filtración de información] → no cachear secretos detectables, restringir
  permisos y redactar valores sensibles en metadatos.
- [Resultados inesperados] → modo desactivado por defecto y métricas de hit,
  miss e invalidación visibles.

## Migration Plan

Introducir la capacidad desactivada por defecto, validar con el ejecutor falso,
habilitarla de forma gradual y permitir borrar sólo sus entradas derivadas sin
afectar runs ni worktrees. El rollback consiste en desactivarla.
