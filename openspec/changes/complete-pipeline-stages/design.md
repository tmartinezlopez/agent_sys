## Context

El runtime archivado ya crea worktrees, persiste un ledger y ejecuta de forma
real `spec-writer → gate_spec → implementer`. `stage-guard.py` y
`roles.json` conocen las seis etapas, pero `run-pipeline.sh` y
`resume-run.sh` sólo materializan las dos primeras etapas escribibles. El
estado persistido debe seguir siendo la única fuente de verdad y los agentes
no deben integrar ni publicar cambios.

## Goals / Non-Goals

**Goals:**

- Convertir el flujo posterior a `implementer` en una máquina de etapas
  reanudable y observable.
- Mantener un único `run_id`, worktree, ledger y conjunto de evidencias por
  feature.
- Hacer explícito cuándo se ejecuta `ui-reviewer` y cuándo una feature queda
  lista para revisión humana final.
- Cubrir éxito, fallo, interrupción, reanudación y no duplicación con pruebas
  deterministas y una prueba E2E representativa.

**Non-Goals:**

- Implementar una interfaz web o un watchdog persistente.
- Conceder a ningún agente permisos de merge, push o publicación.
- Añadir roles nuevos o cambiar los sandboxes declarados.

## Decisions

### Máquina de etapas derivada del ledger

Se mantendrá una única lista ordenada de etapas y un plan read-only que derive
la siguiente etapa desde eventos y estados. `resume-run.sh` dejará de codificar
únicamente `implementer` y despachará la etapa indicada por ese plan. Cada
despacho y finalización seguirá registrando `role`, `taskId`, `stageDir` y
resultado; una etapa completada no volverá a despacharse.

Alternativa descartada: añadir cuatro scripts de reanudación independientes.
Duplicaría las precondiciones y haría más fácil que cada script interpretase el
ledger de forma distinta.

### Un helper común para ejecutar etapas

La construcción de prompts, el wrapper Codex, el guard de Git y la persistencia
de resultados se centralizarán en un helper reutilizable por todas las etapas.
Los roles read-only conservarán sus sandboxes del catálogo y `implementer`
seguirá siendo el único rol escribible después del spec.

Alternativa descartada: ejecutar todos los roles desde un único prompt Codex.
Perdería aislamiento, evidencia por etapa, reanudación precisa y control de
permisos.

El perfil de `test-runner` usa `gpt-5.6-luna` con razonamiento `high`, porque
`gpt-5.3-codex` no está disponible para la cuenta ChatGPT usada por Codex CLI.
La prueba E2E dejó constancia del rechazo del modelo anterior antes de ejecutar
la etapa; el catálogo y el contexto del proyecto se mantienen alineados con el
perfil disponible.

### UI explícita en los metadatos del run

`new-feature.sh` aceptará una opción explícita `--ui` y la persistirá en
`run.json`. El plan ejecutará `ui-reviewer` sólo cuando ese atributo sea cierto.
No se inferirá la afectación de interfaz mediante texto libre del objetivo ni
mediante heurísticas sobre nombres de archivos.

Alternativa descartada: ejecutar siempre `ui-reviewer`. Añadiría coste y ruido
a features de backend y rompería la condición contractual de etapa opcional.

### Gate final separado del estado completado

Después de QA correcto se registrará `gate_release` pendiente. La consulta de
estado distinguirá `qa completed` de `ready_for_review` y de `completed` tras
aprobación humana. `resume-run.sh` podrá continuar desde un gate final aprobado
o informar claramente de que sigue pendiente; nunca realizará integración.

### Contrato de fallo y reanudación

Un resultado Codex distinto de cero, timeout o ausencia de evento de
finalización dejará la etapa abierta/fallida y conservará stdout, stderr y
`result.json`. La reanudación podrá repetir esa etapa concreta, pero no las
anteriores completadas. Las consultas permanecerán read-only y no repararán el
ledger implícitamente.

## Risks / Trade-offs

- **[Una etapa read-only puede producir un diagnóstico no accionable]** → El
  prompt y el resultado persistido exigirán resumen, verificaciones y estado
  explícito; la corrección seguirá siendo una decisión humana o una nueva
  reanudación.
- **[Los cambios de esquema del ledger pueden romper runs antiguos]** → Se
  conservarán nombres de eventos existentes y se harán opcionales los nuevos
  campos; los runs anteriores seguirán pudiendo consultarse.
- **[El gate final puede dejar features acumuladas]** → `pipelines-status` y
  `run-health-check` mostrarán el gate pendiente y el operador podrá decidir o
  parar el run sin tocar el worktree.
- **[La revisión UI requiere contexto visual que Codex CLI no siempre tiene]**
  → La etapa será condicional y read-only; si necesita navegador o evidencia
  adicional, dejará el diagnóstico para revisión humana en vez de inventar un
  resultado.

## Migration Plan

1. Añadir el plan multi-etapa y el helper común manteniendo compatibilidad con
   los eventos del slice actual.
2. Añadir la ejecución secuencial de `test-runner`, `reviewer`, `ui-reviewer`
   condicional y `qa`.
3. Añadir `gate_release`, consultas actualizadas y reanudación desde cualquier
   etapa abierta.
4. Ejecutar pruebas deterministas, validar OpenSpec y repetir una E2E real en
   un worktree temporal.
5. Si hay regresión, conservar la rama de feature y revertir el commit del
   bloque sin alterar los ledgers de runs existentes.

## Open Questions

Ninguna que cambie el contrato o el desglose de implementación.
