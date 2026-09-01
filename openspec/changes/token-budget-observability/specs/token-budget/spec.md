## Purpose

Hace visible y controlable el consumo de tokens del pipeline, incluso cuando la
versión del ejecutor sólo informa una parte de las métricas disponibles.

## ADDED Requirements

### Requirement: El uso se registra por etapa y run

El runtime SHALL conservar por cada despacho las métricas de tokens que el
ejecutor proporcione, SHALL distinguir valores `unknown` de cero y SHALL
exponer acumulados por etapa y run.

#### Scenario: Ejecutor informa uso
- **WHEN** Codex devuelve métricas de entrada, salida o razonamiento
- **THEN** el runtime las persiste y las incluye en el informe del run

#### Scenario: Ejecutor no informa uso
- **WHEN** Codex no devuelve una métrica
- **THEN** esa métrica queda como `unknown` y el run no la presenta como cero

### Requirement: El presupuesto bloquea nuevos despachos

El runtime SHALL aceptar un presupuesto opcional por run y SHALL impedir un
nuevo despacho cuando el uso conocido supere ese presupuesto, conservando el
ledger y explicando el motivo.

#### Scenario: Presupuesto superado
- **WHEN** el acumulado conocido supera el límite antes de una etapa
- **THEN** no se lanza Codex y se registra `budget_blocked` con uso y límite

#### Scenario: Presupuesto desactivado
- **WHEN** no se configura presupuesto
- **THEN** el runtime conserva el control por número de despachos sin bloquear por tokens
