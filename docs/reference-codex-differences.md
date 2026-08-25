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
- El primer slice implementado es spec-writer → gate → implementer. Los
  roles posteriores están declarados, pero su orquestación completa queda para
  el siguiente bloque.
- No se incluye todavía revisión UI mediante bridge de navegador, watchdog
  completo ni una operación ship-feature.sh.
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
