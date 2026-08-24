## Context

El gate no es un séptimo rol: es una decisión del operador dentro del run.
Debe conservar el mismo `run_id` y no introducir memoria fuera de `run.json` y
`events.jsonl`.

## Decisions

- Añadir al estado raíz un objeto `gates.spec-review` con `status` en
  `pending`, `approved` o `rejected`.
- Exponer una operación CLI explícita equivalente a:
  `agent_sys --gate spec-review --decision approve|reject --run-id <id>`.
- Al aprobar, la operación cargará el ledger y continuará las etapas restantes
  desde `implementer`; al rechazar, bloqueará las etapas restantes.
- La identidad del operador se tomará de `--operator` y será obligatoria para
  una decisión.
- No se permitirá cambiar una decisión ni aprobar un run que no tenga el gate
  pendiente.
- El pipeline normal se detendrá después de `spec-writer` cuando no se indique
  una decisión previa.

## Non-goals

- No implementar todavía pausa/parada general, watchdog ni reanudación tras
  fallos arbitrarios.
- No añadir una interfaz web ni interacción con navegador.
- No permitir aprobación automática por otro agente.

## Flow

1. `pipeline` ejecuta y valida `spec-writer`.
2. El coordinador crea `spec-review=pending` y detiene el run.
3. El operador inspecciona los artefactos y ejecuta la orden de decisión.
4. Una aprobación reanuda el mismo run desde `implementer`; un rechazo lo
   cierra como bloqueado.

