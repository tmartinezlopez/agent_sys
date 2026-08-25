## MODIFIED Requirements

### Requirement: El run tiene un ledger único y reconstruible

Cada ejecución SHALL tener un `run_id` único y un ledger en el worktree con
metadatos inmutables, eventos append-only y estado derivado. Las operaciones de
consulta SHALL reconstruir el estado desde el ledger y no desde memoria del
proceso coordinador. Cada etapa aplicable SHALL conservar su propio prompt,
comando, resultado, stdout y stderr bajo el mismo run.

#### Scenario: Run inicializado

- **WHEN** se crea una feature ejecutable
- **THEN** existe un run con `run.json`, `events.jsonl` y estado derivado, y el
  primer evento identifica la creación del run

#### Scenario: Consulta no mutante

- **WHEN** el operador consulta status, logs, salud o informe
- **THEN** la consulta devuelve datos del ledger sin añadir eventos ni cambiar
  el estado persistido

#### Scenario: Evidencia multi-etapa

- **WHEN** una etapa posterior se despacha en un run existente
- **THEN** su evidencia queda correlacionada con el mismo `run_id` y el estado
  identifica de forma separada cada rol ejecutado

### Requirement: Codex se despacha sólo con roles declarados y en orden

El runtime SHALL lanzar procesos externos mediante `codex exec` usando uno de
los roles declarados del pipeline y SHALL impedir el uso de agentes genéricos
como sustitutos de una etapa. El orden aplicable SHALL ser
`spec-writer → implementer → test-runner → reviewer → ui-reviewer → qa`,
omitiendo `ui-reviewer` cuando la feature no esté marcada como afectada por la
interfaz. Ninguna etapa posterior SHALL iniciarse si su predecesora obligatoria
no ha terminado correctamente.

#### Scenario: Despacho del vertical slice inicial

- **WHEN** un run nuevo supera sus precondiciones
- **THEN** se lanza `spec-writer` con su contrato Codex y no se lanza
  `implementer` antes de completar el gate del spec

#### Scenario: Continuación del pipeline

- **WHEN** `implementer` termina correctamente y el gate de implementación está
  aprobado
- **THEN** se despacha `test-runner`, después `reviewer`, después `qa`, y se
  inserta `ui-reviewer` sólo para una feature marcada como UI

#### Scenario: Intento fuera de orden

- **WHEN** se solicita una etapa cuya predecesora no ha terminado o cuyo rol no
  pertenece al catálogo
- **THEN** el runtime bloquea el despacho, registra la razón y no inicia Codex

### Requirement: El gate humano controla el paso a implementación

Después de un `spec-writer` correcto, el runtime SHALL abrir un gate humano
pendiente y SHALL detener el pipeline hasta una decisión explícita. La
decisión SHALL indicar aprobación, cambios o descarte y quedar registrada con
operador, motivo y timestamp. Después de completar QA, el runtime SHALL abrir
un gate final de revisión humana antes de considerar la feature lista para
integración.

#### Scenario: Gate pendiente

- **WHEN** `spec-writer` termina correctamente
- **THEN** el ledger contiene un gate pendiente y `implementer` permanece sin
  despachar

#### Scenario: Aprobación del gate

- **WHEN** el operador aprueba el gate del spec
- **THEN** el ledger registra la aprobación y el runtime puede despachar
  `implementer` en el mismo run y worktree

#### Scenario: Cambios o descarte

- **WHEN** el operador solicita cambios o descarta la especificación
- **THEN** el runtime no despacha `implementer`, conserva la decisión y deja el
  run en un estado que pueda inspeccionarse

#### Scenario: Gate final de integración

- **WHEN** todas las etapas aplicables, incluida QA, terminan correctamente
- **THEN** el ledger abre un gate final pendiente y no se ejecutan merge ni push
  hasta una decisión humana posterior

### Requirement: Un run puede reanudarse sin duplicar trabajo completado

La reanudación SHALL derivar la primera etapa pendiente o abierta desde el
ledger, SHALL reutilizar el mismo `run_id` y SHALL registrar un evento de
reanudación. No SHALL repetir etapas ya completadas ni volver a pedir un gate ya
aprobado. Si una etapa posterior falla o queda abierta, la reanudación SHALL
volver a esa etapa y conservar las evidencias anteriores.

#### Scenario: Reanudación después de aprobar el gate

- **WHEN** un run tiene `spec-writer` completado y el gate aprobado
- **THEN** la reanudación inicia en `implementer`, conserva el `run_id` y no
  vuelve a ejecutar `spec-writer`

#### Scenario: Reanudación de una etapa posterior

- **WHEN** `test-runner`, `reviewer`, `ui-reviewer` o `qa` queda abierta o falla
- **THEN** el plan de reanudación identifica esa etapa como la primera pendiente
  y no repite las etapas anteriores completadas

#### Scenario: Run muerto a mitad de etapa

- **WHEN** existe un despacho sin evento de finalización
- **THEN** el plan de reanudación identifica esa etapa como abierta y no la
  declara completada por defecto

### Requirement: La integración requiere revisión humana

El runtime SHALL dejar el trabajo en la rama de feature para revisión humana y
NO SHALL ejecutar merge o push automáticamente. La integración y limpieza del
worktree SHALL ser operaciones separadas del pipeline de agentes. El run sólo
podrá marcarse listo para integración después de que el gate final haya sido
decidido explícitamente.

#### Scenario: Run terminado

- **WHEN** todas las etapas aplicables terminan correctamente y el operador
  aprueba el gate final
- **THEN** el runtime registra el cierre y deja disponible el diff de la rama
  para revisión o integración humana

#### Scenario: Intento de publicación automática

- **WHEN** una etapa o el coordinador intenta hacer merge a la rama principal o
  publicar en GitHub
- **THEN** la operación se rechaza y el run conserva su evidencia

#### Scenario: QA no aprobado

- **WHEN** QA falla o el operador no aprueba el gate final
- **THEN** el run no se marca listo para integración y permanece reanudable o
  inspeccionable con toda su evidencia
