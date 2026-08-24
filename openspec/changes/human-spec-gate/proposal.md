## Why

El pipeline puede generar una especificación válida y empezar a implementar en
la misma ejecución. Eso elimina la revisión deliberada del operador, que debe
decidir si el alcance y el diseño son correctos antes de permitir cambios en
el checkout.

## What Changes

- Añadir un gate humano persistente `spec-review` entre `spec-writer` e
  `implementer`.
- Detener el pipeline con el gate en estado `pending` hasta una decisión
  explícita del operador.
- Añadir una orden CLI para aprobar o rechazar el gate por `run_id`.
- Reanudar desde el mismo run tras aprobar, sin repetir etapas ya completadas.
- Registrar decisión, operador, motivo, timestamps y eventos.

## Capabilities

### New Capabilities

- `human-spec-gate`: decisión humana persistente y reanudación controlada tras
  la especificación.

### Modified Capabilities

- Ninguna.

## Impact

- Afecta al ledger, al coordinador `pipeline` y a `src/agent_sys/cli.py`.
- Añade el contrato del gate y pruebas de pausa, aprobación, rechazo y
  reanudación.
- No añade roles, modelos ni dependencias externas.

