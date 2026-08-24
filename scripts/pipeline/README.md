# Runtime del pipeline

Esta carpeta contiene la mecánica operativa del sistema: paths, worktrees,
ledger, despacho Codex, reanudación y consultas. Los contratos de los roles se
mantienen separados de esta capa.

Las funciones de `lib-paths.sh` son la única fuente de verdad para nombres de
worktrees, ramas, ventanas y runs. Los scripts deben ser seguros con
`set -euo pipefail` y no deben integrar ramas ni publicar cambios por sí solos.
