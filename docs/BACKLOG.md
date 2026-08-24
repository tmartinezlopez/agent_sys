# Backlog de construcción

Cada bloque se inicia solo cuando sus prerrequisitos están verificados. Un
check significa que existe evidencia local; no significa que el sistema final
ya esté completo.

## 0. Bootstrap

- [x] Convertir este directorio en checkout Git y conservar el historial remoto
  mediante `origin/main`. Evidencia: `git rev-parse --show-toplevel`, historial
  local fusionado y ningún `push` realizado.
- [x] Instalar e inicializar OpenSpec para Codex. Evidencia: `openspec doctor`
  devuelve `OpenSpec root: ok`.
- [x] Verificar herramientas. Evidencia: OpenSpec `1.10.0`, Codex CLI
  `0.149.1`, tmux `3.6`; `codex login status` devuelve `Logged in using ChatGPT`.
- [x] Completar `openspec/config.yaml` con el contexto Python/Bash y comandos
  reales de calidad.

## 1. Contrato global

Prerrequisito: bootstrap de herramientas.

- [x] Crear el catálogo de los seis roles con modelo, reasoning, sandbox,
  timeout, reintentos, prompt y artefactos esperados.
- [x] Definir estados, eventos, códigos de salida y transiciones válidas.
- [x] Verificar el contrato con tests de configuración y transiciones.

## 2. Estado y ledger

Prerrequisito: contrato global.

- [x] Implementar `run.json`, `events.jsonl`, resultados de etapa y resumen.
- [x] Implementar reconstrucción de un run desde disco.
- [x] Verificar éxito, fallo, timeout y bloqueo con tests dirigidos.

## 3. Runtime tmux

Prerrequisitos: contrato global y, para worktrees, checkout Git válido.

- [x] Crear/reutilizar sesión del proyecto y ventana `coordinator`.
- [x] Crear ventanas nombradas por run y rol.
- [x] Verificar que no se modifican sesiones o procesos ajenos.

## 4. Lanzador Codex

Prerrequisitos: contrato global y estado persistente.

- [x] Construir la orden real `codex exec` desde la configuración del rol.
- [x] Aplicar modelo, reasoning, sandbox, directorio, prompt y timeout.
- [x] Persistir stdout, stderr, código de salida y comando exacto.
- [x] Verificar éxito, error de proceso, binario ausente y timeout.

## 5. Primera ejecución completa

Prerrequisitos: estado, tmux y lanzador Codex.

- [x] Lanzar una etapa desde el coordinador dentro de una ventana tmux.
- [x] Registrar inicio, finalización, resultado y artefactos.
- [ ] Verificar que una etapa fallida impide lanzar la siguiente.

## 6. Roles

Prerrequisito: primera ejecución completa.

- [ ] Implementar `spec-writer` con OpenSpec real y probar sus artefactos.
- [ ] Implementar gate humano posterior al spec y persistir su decisión.
- [ ] Implementar `implementer` y probar modificaciones en un worktree.
- [ ] Implementar `test-runner` en solo lectura.
- [ ] Implementar `reviewer` en solo lectura.
- [ ] Implementar `ui-reviewer` como etapa condicional.
- [ ] Implementar `qa` en solo lectura.

## 7. Recuperación y operación

Prerrequisito: todas las etapas básicas funcionando.

- [ ] Implementar watchdog para detectar runs sin actividad.
- [ ] Implementar pausa, parada segura y reanudación desde el último estado.
- [ ] Implementar status, logs, resumen e inspección del run.
- [ ] Verificar un run reanudado y que no duplica etapas completadas.
