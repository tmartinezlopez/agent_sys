## Why

La implementación anterior reproducía parte del comportamiento, pero no la
arquitectura operativa del sistema de referencia: trabajaba directamente sobre
el checkout, concentraba el runtime en Python y no tenía un ciclo de vida
aislado por feature. Necesitamos reconstruir una base fiel al modelo de
worktrees, ledger y operación de referencia, sustituyendo únicamente el
backend de Claude por procesos reales de Codex CLI.

## What Changes

- Crear un runtime operativo con worktree y rama `feature/<item>` por feature.
- Persistir cada ejecución en un ledger event-sourced con estado derivado,
  eventos append-only, resumen e informe.
- Añadir un adaptador de despacho que ejecute los roles declarados mediante
  `codex exec`, con sus prompts, modelos, sandbox y artefactos explícitos.
- Implementar el vertical slice `spec-writer → gate humano → implementer` sobre
  el mismo `run_id`, incluyendo pausa, aprobación y reanudación.
- Añadir operaciones de estado, logs, salud y reanudación sobre el ledger.
- Mantener la revisión humana antes de integrar una feature y prohibir que el
  runtime haga merge o push automáticamente.
- Mantener el runtime dividido entre scripts operativos Bash y helpers Python,
  en lugar de convertir todo el coordinador en una aplicación Python monolítica.

### No cambia en este bloque

- No se migran literalmente los agentes, comandos o hooks específicos de
  Claude; se reemplazan por contratos compatibles con Codex.
- No se implementan todavía todos los roles posteriores, revisión UI real,
  watchdog completo ni cierre automático de features.
- No se publica nada en GitHub ni se modifica `main` desde el runtime.

## Capabilities

### New Capabilities

- `reference-codex-runtime`: ciclo de vida aislado, ledger observable y
  despacho de Codex para un pipeline reanudable.

### Modified Capabilities

- Ninguna.

## Impact

- Añade `scripts/pipeline/` como runtime operativo y un adaptador Codex para
  los roles.
- Añade convenciones `.pipeline/` para runs locales, toolchain y punteros de
  ejecución, sin versionar el estado efímero.
- Cambia la entrada pública de ejecución para crear primero worktree, rama y
  ledger antes de lanzar Codex.
- Reemplaza el modelo de ejecución sobre el checkout actual por aislamiento
  por feature; los consumers de estado deberán leer el ledger y no memoria del
  proceso coordinador.
- Requiere Git, Bash, Python, tmux opcional, OpenSpec y Codex CLI autenticado.
