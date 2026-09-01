# agent_sys

Runtime reutilizable para coordinar un pipeline de trabajo con Codex CLI,
worktrees Git, gates humanos y evidencia auditable.

## Documentación

- [Guía de uso](GUIA-USO.md): instalación y operación diaria.
- [Arquitectura](docs/ARCHITECTURE.md): piezas, responsabilidades y límites.
- [Flujo del pipeline](docs/PIPELINE.md): stages, gates, runs y recuperación.
- [Adopción](docs/ADOPTION.md): instalación en otro repositorio.
- [Actualización](docs/UPDATING.md): cómo propagar cambios a consumidores.
- [Adaptación por proyecto](docs/PROJECT-CONTRACT.md): comandos y contratos que aporta cada proyecto.
- [Backlog](docs/backlog.md): mejoras pendientes del runtime.

La validación local completa se ejecuta con:

```bash
bash tests/check-all.sh
```

El runtime no hace `merge`, `push` ni limpieza automática de worktrees.
