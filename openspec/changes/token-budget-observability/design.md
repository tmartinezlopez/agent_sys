## Context

El runtime registra el resultado del proceso Codex y aplica
`PIPELINE_MAX_DISPATCHES`, pero el uso de tokens puede venir ausente o cambiar
de forma entre versiones del CLI.

## Goals / Non-Goals

**Goals:** normalizar métricas disponibles, conservar su origen, sumar por run
y detener nuevos despachos de forma segura al superar el presupuesto.

**Non-Goals:** estimar silenciosamente tokens ausentes, facturar costes,
controlar una sesión interactiva ya iniciada o cambiar el formato de salida de
Codex.

## Decisions

- Guardar un objeto de uso por etapa con campos opcionales y estado explícito
  `reported` o `unknown`; la ausencia no se convertirá en cero.
- Calcular el acumulado leyendo la evidencia/ledger, para que reanudaciones y
  consultas sean reproducibles.
- Comprobar el presupuesto antes de despachar y registrar `budget_blocked` con
  el uso acumulado y el umbral. La alternativa de matar una etapa activa se
  descarta por seguridad y pérdida de evidencia.
- Mantener el límite de despachos como control independiente; ambos límites
  deben cumplirse.

## Risks / Trade-offs

- [CLI incompatible] → parser tolerante, versión/origen registrado y pruebas
  con uso ausente.
- [Métrica parcial] → distinguir desconocido de cero y no prometer un coste
  exacto.
- [Reanudación] → sumar sólo etapas finalizadas y usar identidad de etapa/run
  para evitar duplicados.

## Migration Plan

Añadir el presupuesto sin activarlo por defecto, probar el ejecutor falso,
activar límites explícitos en ejecuciones reales y documentar la semántica de
uso desconocido. Desactivar el presupuesto restaura el comportamiento actual.
