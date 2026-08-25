## 1. Contratos de estado y planificación de etapas

- [x] 1.1 Extender los metadatos de run para persistir si la feature afecta a
  UI, manteniendo compatibilidad con runs antiguos; verificar creación y
  lectura con y sin el atributo.
- [x] 1.2 Ampliar el estado derivado y `resume-plan` para representar las seis
  etapas, gates y estados abierta/fallida/completada; verificar que el plan
  devuelve la primera etapa pendiente sin mutar el ledger.
- [x] 1.3 Añadir el gate final de release y sus transiciones aprobada,
  cambios y descarte; verificar que un run no se marca listo para integración
  sin decisión humana.

## 2. Despacho y reanudación multi-etapa

- [x] 2.1 Extraer un ejecutor común de etapas que persista prompt, comando,
  stdout, stderr, resultado y exit code para cualquier rol declarado; verificar
  éxito, timeout, binario ausente y guard de merge/push.
- [x] 2.2 Implementar los prompts y precondiciones de `test-runner`, `reviewer`,
  `ui-reviewer` y `qa` con los modelos y sandboxes de `roles.json`; verificar
  que no se acepta ningún rol genérico.
- [x] 2.3 Extender `resume-run.sh` para avanzar por todas las etapas aplicables
  en orden, registrar cada despacho en el mismo `run_id` y no repetir etapas
  completadas; verificarlo con un Codex falso determinista.
- [x] 2.4 Añadir la opción explícita `--ui` al inicio de una feature y ejecutar
  `ui-reviewer` sólo cuando esté persistida; verificar los flujos UI y no-UI.
- [x] 2.5 Gestionar fallos e interrupciones en cualquier etapa posterior,
  dejando evidencia y reanudando desde la etapa abierta; verificar que las
  etapas anteriores no se duplican.

## 3. Operación y observabilidad

- [x] 3.1 Actualizar `status`, health-check, logs y report para mostrar todas
  las etapas, gates y el estado `ready_for_review`; verificar consultas
  multi-run sin mutar `events.jsonl`.
- [x] 3.2 Revisar parada segura para runs con etapas posteriores y tmux,
  manteniendo el worktree intacto y sin afectar ventanas ajenas; verificarlo
  con el test de seguridad de parada.
- [x] 3.3 Documentar el flujo completo, la opción `--ui`, los estados de gate
  y el límite de que merge/push siguen siendo humanos; verificar comandos con
  ejemplos reproducibles.

## 4. Verificación determinista

- [x] 4.1 Cubrir el flujo completo no-UI con `spec-writer`, gate, implementer,
  test-runner, reviewer y qa; verificar un único run, orden correcto y gate
  final pendiente.
- [x] 4.2 Cubrir el flujo UI y comprobar la inclusión única de `ui-reviewer`,
  junto con el orden y modelos registrados; verificar ausencia de la etapa en
  un flujo no-UI.
- [x] 4.3 Cubrir fallo, timeout y reanudación desde cada etapa posterior;
  verificar que se conserva la evidencia y no se repiten roles completados.
- [x] 4.4 Ejecutar la batería completa de contratos, operaciones read-only,
  guard de Git, parada segura y sintaxis Bash/Python; verificar todos los
  resultados `PASS`.

## 5. Validación E2E y cierre del bloque

- [x] 5.1 Ejecutar una E2E con Codex CLI real para una feature no-UI,
  comprobando worktree aislado, ledger, gates, seis etapas aplicables y
  `run_id` único.
- [x] 5.2 Ejecutar una E2E con Codex CLI real para una feature UI o justificar
  con evidencia reproducible el camino condicional; verificar que
  `ui-reviewer` aparece una sola vez.
- [x] 5.3 Validar OpenSpec con `--strict`, actualizar diferencias deliberadas
  y dejar el bloque archivado sólo cuando no queden tareas pendientes.
