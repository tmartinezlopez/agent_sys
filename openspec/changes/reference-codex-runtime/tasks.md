## 1. Base del runtime y convenciones de rutas

- [x] 1.1 Crear la estructura mínima de `scripts/pipeline/`, `.pipeline/` y
  configuración versionada del runtime, y verificar que `bash -n` pasa para
  todos los scripts públicos.
- [x] 1.2 Portar la convención única de paths para repo, worktree, rama,
  ventana tmux y directorio de runs, y verificarla con casos de nombres
  válidos, espacios y overrides explícitos.
- [x] 1.3 Implementar creación de worktree y rama `feature/<item>` sin lanzar
  agentes, y verificar que el checkout principal permanece limpio.

## 2. Ledger event-sourced

- [x] 2.1 Implementar inicialización de run con metadatos inmutables,
  `events.jsonl`, puntero local y estado derivado; verificar creación,
  permisos y primer evento.
- [x] 2.2 Implementar escritura durable y validada de eventos, reconstrucción
  de estado, `show` y `summary`; verificar que un evento inválido no altera el
  ledger y que la reconstrucción es determinista.
- [x] 2.3 Implementar `resume-plan` read-only para derivar etapa completada,
  etapa abierta, gate y etapa de reanudación; verificar que no modifica ningún
  archivo del run.

## 3. Adaptador Codex y contratos de etapa

- [x] 3.1 Declarar exactamente los seis roles y su configuración Codex en un
  único catálogo, y verificar que no se acepta un rol genérico ni un modelo
  ficticio.
- [x] 3.2 Implementar el wrapper de `codex exec` que persista comando, prompt,
  stdout, stderr, exit code y resultado; verificar éxito, fallo, timeout y
  binario ausente.
- [x] 3.3 Implementar precondiciones de orden, gate y sandbox por etapa, y
  verificar que un despacho fuera de orden no inicia Codex y deja evidencia.

## 4. Vertical slice spec → gate → implementer

- [ ] 4.1 Lanzar `spec-writer` desde el worktree creado y validar sus artefactos
  OpenSpec reales; verificar el run con Codex en un proyecto temporal Git.
- [ ] 4.2 Abrir y persistir el gate humano después de `spec-writer`, incluyendo
  aprobación, cambios y descarte; verificar que `implementer` no se lanza con
  el gate pendiente o descartado.
- [ ] 4.3 Implementar `new-feature.sh` para crear worktree, inicializar ledger
  y lanzar el slice con tmux opcional; verificar fallback foreground sin tmux.
- [ ] 4.4 Implementar `resume-run.sh` sobre el mismo `run_id` y worktree,
  respetando gates y evitando repetir etapas completadas; verificar una
  reanudación real desde `implementer`.

## 5. Operación y seguridad del slice

- [ ] 5.1 Implementar `status`, logs, health-check y report del ledger como
  consultas read-only; verificar listado multi-run, run desconocido y ausencia
  de mutaciones.
- [ ] 5.2 Implementar parada segura limitada a la ventana/proceso del run y
  registrar su resultado; verificar que no afecta sesiones tmux ajenas.
- [ ] 5.3 Impedir merge y push desde el runtime de agentes y dejar la rama de
  feature lista para revisión humana; verificar el bloqueo en un repositorio
  temporal.

## 6. Verificación de arquitectura

- [ ] 6.1 Ejecutar una prueba end-to-end real del vertical slice con Codex CLI,
  comprobando worktree aislado, ledger, gate, reanudación y mismo `run_id`.
- [ ] 6.2 Ejecutar las pruebas deterministas del runtime, validar OpenSpec con
  `--strict` y documentar las diferencias deliberadas frente al repositorio de
  referencia antes de incorporar más roles.
