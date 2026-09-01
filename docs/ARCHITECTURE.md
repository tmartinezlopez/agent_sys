# Arquitectura

## Separación de responsabilidades

`agent_sys` es la copia maestra de la metodología. Un proyecto consumidor la
instala como `metodologia/` y conserva su propio código, OpenSpec, backlog y
configuración.

El coordinador (`coordinator.sh`) mantiene la visión global y es el único que
decide el desglose, el orden y los gates. Los roles son trabajadores
especializados: `spec-writer`, `implementer`, `test-runner`, `reviewer`,
`ui-reviewer` y `qa`. No lanzan otros agentes ni coordinan el proyecto.

## Componentes

- `scripts/pipeline/`: runtime operativo: worktrees, despacho, ledger, gates,
  reanudación, diagnóstico y limpieza de runs.
- `scripts/pipeline/roles/`: launchers explícitos por rol.
- `.pipeline/runs/`: evidencia local de ejecuciones; no es código funcional.
- `tests/`: contratos y pruebas deterministas del runtime.
- `openspec/`: contrato y propuestas de evolución de la metodología.
- `docs/` y `GUIA-USO.md`: documentación operativa.

## Límites de seguridad

Cada feature se ejecuta en su worktree y rama propios. Codex real requiere
activación y límite explícitos. El guard de Git impide `merge` y `push` desde
los agentes; la integración final siempre la decide una persona.
