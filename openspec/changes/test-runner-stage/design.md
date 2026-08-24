## Context

El runtime permite declarar `test-runner` como etapa read-only, pero todavía
usa un prompt genérico y no ejecuta el comando de pruebas del proyecto. La
configuración actual verifica el proyecto con `PYTHONPATH=src pytest -q`.

## Goals / Non-Goals

**Goals:**

- Ejecutar pruebas reales después de `implementer`.
- Evitar modificaciones del checkout desde esta etapa.
- Registrar evidencia legible por `reviewer` y `qa`.

**Non-Goals:**

- Corregir automáticamente el código o las pruebas.
- Elegir dinámicamente herramientas no declaradas.
- Implementar todavía reviewer, ui-reviewer o qa.

## Decisions

- El comando de pruebas será una configuración explícita del proyecto:
  `PYTHONPATH=src pytest -q`; no se inferirá desde la respuesta de Codex.
- El coordinador validará el handoff de implementer antes de lanzar el proceso.
- El sandbox será `read-only` y la etapa solo podrá producir artefactos dentro
  de `runs/<run_id>/stages/test-runner`.
- El resultado incluirá comando, código de salida, logs y resumen; un proceso
  posterior consumirá esos ficheros.

## Risks / Trade-offs

- [Risk] El proyecto puede necesitar un comando distinto → Mitigation: dejarlo
  como configuración explícita y verificarlo antes de lanzar.
- [Risk] Las pruebas pueden tardar o bloquearse → Mitigation: reutilizar el
  timeout del runtime y marcar la etapa como `failed`.
- [Risk] Herramientas de prueba escriben caches → Mitigation: sandbox read-only
  y registrar cualquier error de permisos como fallo.
