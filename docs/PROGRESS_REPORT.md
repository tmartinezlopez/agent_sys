# Informe de progreso de `agent_sys`

## Resumen ejecutivo

`agent_sys` ya tiene construido el esqueleto funcional de un coordinador de
agentes basado en procesos externos de Codex CLI. Puede crear una ejecución,
lanzar las etapas declaradas, guardar toda la evidencia en disco, detenerse
ante una revisión humana y continuar después de una aprobación.

La parte que falta es principalmente operativa: recuperación ante procesos
inactivos, pausa y parada segura, y reanudación general desde el último punto
válido. No falta el mecanismo básico del gate de especificación; ese caso ya
está probado.

## Qué está construido

### 1. Base del proyecto

- Checkout Git local.
- OpenSpec inicializado y validable.
- Integración con Codex CLI real.
- Ejecución mediante Python/Bash y, cuando se usa, tmux.

### 2. Contrato del pipeline

El pipeline declara seis roles y los ejecuta en este orden:

`spec-writer → implementer → test-runner → reviewer → ui-reviewer → qa`

Cada rol tiene modelo, nivel de razonamiento, sandbox, timeout, reintentos,
prompt contractual y artefactos esperados. `ui-reviewer` es condicional: se
omite si el cambio no afecta a la interfaz.

### 3. Estado y observabilidad

Cada ejecución se guarda en `runs/<run_id>/` con:

- `run.json`: estado actual, etapas, gates y metadatos.
- `events.jsonl`: historial de eventos en modo append-only.
- `stages/<stage>/`: prompt, stdout, stderr, resultado y artefactos de cada
  etapa.

También están implementados los estados `pending`, `running`, `passed`,
`failed`, `blocked` y `skipped`, con transiciones controladas.

### 4. Gate humano de especificación

Después de `spec-writer`, el pipeline crea el gate `spec-review` en estado
`pending` y no inicia `implementer` automáticamente.

El operador puede aprobar o rechazar desde la CLI. La decisión guarda operador,
motivo y timestamp. Una aprobación continúa desde `implementer` conservando
el mismo `run_id`; un rechazo bloquea las etapas restantes.

### 5. Operaciones de consulta

Ya están disponibles:

```bash
./scripts/run.sh --status --runs-dir runs
./scripts/run.sh --status --run-id <run_id> --runs-dir runs
./scripts/run.sh --logs --run-id <run_id> --runs-dir runs
./scripts/run.sh --inspect --run-id <run_id> --runs-dir runs
```

`status` muestra el estado resumido, `logs` devuelve los eventos del ledger e
`inspect` combina el estado completo con los artefactos encontrados.

## Evidencia disponible

- Prueba real con Codex CLI en un proyecto temporal Git.
- El run real `20260824T113511Z-b8a7eec4`:
  - `spec-writer`: `passed`.
  - `spec-review`: `pending` → `approved`.
  - `implementer`: iniciado después de aprobar, sin repetir `spec-writer`.
  - Resultado final: `passed`.
- Suite local: `34 passed`.
- OpenSpec validado con `--strict`.

## Qué falta

### Prioridad inmediata: recuperación y operación

1. **Watchdog**

   Detectar runs o etapas que llevan demasiado tiempo sin actualizar su estado
   o sin producir actividad observable. Debe registrar el diagnóstico sin matar
   procesos de forma indiscriminada.

2. **Pausa y parada segura**

   Añadir órdenes explícitas para solicitar una pausa o detener un run,
   persistiendo la intención y el resultado en `run.json` y `events.jsonl`.
   La parada debe limitarse a procesos y ventanas pertenecientes al run.

3. **Reanudación general**

   Cargar un run existente, localizar la primera etapa no completada y
   continuar desde ahí. Las etapas `passed` o `skipped` no deben ejecutarse de
   nuevo.

4. **Pruebas de recuperación**

   Simular pausa, parada, timeout y reanudación; comprobar que el `run_id`, los
   artefactos y las etapas completadas se conservan.

## Orden recomendado

Primero definir y probar las transiciones de pausa, parada y reanudación.
Después añadir el watchdog, porque necesita conocer cuándo una etapa puede
considerarse inactiva y cómo debe dejar el run para que sea recuperable.

El objetivo de cierre será poder operar un run sin borrar su evidencia y sin
duplicar trabajo ya completado.
