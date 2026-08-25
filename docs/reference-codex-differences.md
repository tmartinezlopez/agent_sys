# Diferencias deliberadas frente a agentic-system

La arquitectura operativa conserva los contratos que merece la pena portar:

- un worktree y una rama feature/<item> por feature;
- un ledger append-only por run con estado derivado;
- gates humanos antes de avanzar;
- reanudación sobre el mismo run_id;
- consultas read-only y parada limitada a la ventana del run;
- revisión humana antes de integrar.

La adaptación a Codex no copia literalmente el sistema de referencia:

- Claude y sus agentes, comandos y hooks se sustituyen por procesos externos
  codex exec con seis roles declarados en roles.json.
- La evidencia de cada etapa son command, result.json, stdout.log y
  stderr.log; no se intenta atribuir transcripts ni tokens de Claude.
- El runtime orquesta `spec-writer → gate_spec → implementer → test-runner →
  reviewer → qa`, e inserta `ui-reviewer` cuando la feature se inicia con
  `--ui`. Después de QA abre `gate_release` para una decisión humana.
- La revisión UI sigue siendo read-only y no incluye un bridge de navegador;
  tampoco hay todavía watchdog completo ni una operación ship-feature.sh.
- El runtime no hace merge, push, limpieza de worktree ni publicación
  automática. La rama queda disponible para inspección humana.

La prueba determinista del slice y de las operaciones pasa. El 25-08-2026 se
ejecutó también la prueba E2E con Codex CLI real (0.149.1) en un worktree
temporal y sin tmux:

- `spec-writer` terminó correctamente, creó y validó un change OpenSpec real
  con `openspec validate --strict` y abrió `gate_spec`.
- El gate se aprobó explícitamente y `resume-run.sh` reanudó el mismo
  `run_id`: `run_e2e-real-20260825_20260825-061244_416134`.
- El ledger terminó en `completed`, con exactamente un despacho de
  `spec-writer`, uno de `implementer` y un evento `run_resumed`; el informe
  confirmó ambas etapas y las consultas no mutaron `events.jsonl`.
- El checkout principal permaneció sin cambios adicionales y no hubo merge ni
  push automáticos.

El bloque de etapas completo añade pruebas deterministas de los flujos UI y
no-UI, reintento desde una etapa fallida y timeout con evidencia persistida.

La validación E2E del bloque completo se ejecutó con Codex CLI real el
25-08-2026, sin tmux y en worktrees temporales:

- No-UI: `run_e2e-full-real_20260825-070626_484784` terminó `completed` con
  `spec-writer`, `implementer`, `test-runner`, `reviewer` y `qa`. El primer
  intento de `test-runner` dejó evidencia del rechazo de `gpt-5.3-codex` por la
  cuenta ChatGPT; el mismo run se reanudó sin repetir las etapas anteriores y
  pasó con `gpt-5.6-luna` y razonamiento `high`.
- UI: `run_e2e-ui-real_20260825-073115_538376` terminó `completed` con las seis
  etapas y un único despacho de `ui-reviewer`; `openspec validate --strict`
  pasó para el change generado.

Durante la E2E UI se detectó y corrigió una condición de carrera: el runner
ahora ejecuta snapshots estables de `resume-run.sh` y `run-stage.sh` dentro del
ledger, de modo que los cambios del implementador en el worktree no alteran la
coordinación activa.
