# Contrato actual del pipeline

El sistema final seguirá la separación descrita en
[`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md). El coordinador recibirá un
objetivo, creará un `run_id`, preparará estado y lanzará etapas externas de
Codex en ventanas tmux nombradas.

El pipeline canónico será:

```text
spec-writer → implementer → test-runner → reviewer → ui-reviewer (si aplica) → qa
```

Cada etapa tendrá configuración propia y producirá prompt, logs, resultado y
artefactos dentro de `runs/<run_id>/stages/<stage_id>/`.

Los estados son:

```text
pending, running, passed, failed, blocked, skipped
```

No se avanza si la etapa anterior no ha pasado o si falta un gate obligatorio.
Los eventos se registrarán en `events.jsonl`; `run.json` será la proyección del
estado actual.

## Estado de implementación

El runtime base ya declara los seis roles, persiste el ledger y puede ejecutar
una etapa real dentro de una ventana tmux propia. El coordinador secuencial de
las seis etapas, gates, reintentos y recuperación sigue pendiente en
[`docs/BACKLOG.md`](docs/BACKLOG.md).

La ejecución productiva usará la cuenta autenticada del Codex CLI mediante
`codex exec`; no se utilizará la API de OpenAI.
