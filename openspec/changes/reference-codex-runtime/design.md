## Context

La rama de reconstrucción parte de una base sin runtime de aplicación. El
repositorio de referencia separa el runtime operativo (`scripts/pipeline`), los
contratos de roles y las comprobaciones; usa worktrees por feature, un ledger
event-sourced y un flujo humano de gate, corrección y cierre. Codex no ofrece
los mismos agentes nativos ni hooks de Claude, por lo que sólo se trasladarán
las garantías y los contratos observables.

## Goals / Non-Goals

**Goals:**

- Validar primero un vertical slice real: worktree, ledger, `codex exec`, gate y
  reanudación.
- Mantener Bash como capa de ciclo de vida y operación, y Python como helper
  para ledger, informes, validaciones y adaptación estructurada a Codex.
- Tener una única fuente de verdad para el estado y eventos de cada run.
- Hacer explícitos los límites de permisos, orden y decisión humana.
- Permitir ampliar después el slice a los seis roles sin cambiar el contrato
  del runtime.

**Non-Goals:**

- Copiar `.claude/agents`, `.claude/commands` o hooks de Claude sin adaptación.
- Implementar todos los roles, UI real, watchdog completo o sincronización de
  sistemas en el primer slice.
- Integrar automáticamente ramas, hacer push o convertir el runtime en un
  servicio persistente.
- Mantener compatibilidad con el runtime Python eliminado de la rama de
  reconstrucción.

## Decisions

### Runtime híbrido guiado por el modelo de referencia

Los scripts Bash gestionarán entrada pública, worktrees, ramas, tmux,
reanudación, parada y composición del flujo. Helpers Python cubrirán JSON,
reconstrucción del ledger, informes y la construcción/evaluación de prompts
Codex. Se elige esta división porque conserva la forma operativa del sistema
de referencia sin forzar parsing complejo de procesos y ledger en Bash.

Alternativa descartada: un coordinador Python monolítico. Era ejecutable, pero
ocultaba el ciclo de vida, mezclaba política y ejecución y produjo la deriva
arquitectónica que motiva este cambio.

### Worktree antes de cualquier agente escribible

`new-feature.sh` usará una convención centralizada de rutas equivalente a
`lib-paths.sh`, con override explícito para el directorio de worktrees. El
nombre de rama, worktree y ventana tmux se derivarán de un único item validado.
El checkout principal sólo se leerá para crear la feature y para operaciones
de cierre autorizadas por el operador.

### Ledger event-sourced y estado derivado

Cada run tendrá un `run.json` inmutable con su identidad y contexto,
`events.jsonl` append-only con flush/fsync, `current-state.json` derivado y
`summary.json` al cerrar. El puntero de run activo será local al worktree y no
se considerará una fuente de verdad independiente. Las consultas serán
read-only y se podrán ejecutar aunque el coordinador haya muerto.

### Codex como adaptador, no como nuevo modelo de roles

Los roles seguirán siendo exactamente `spec-writer`, `implementer`,
`test-runner`, `reviewer`, `ui-reviewer` y `qa`. El adaptador generará órdenes
`codex exec` con el modelo y sandbox declarados por rol, sin aceptar un rol
genérico ni inventar perfiles alternativos. Los contratos de prompt serán
artefactos versionados separados del script que lanza el proceso.

### Gate humano y reanudación como contratos del ledger

El gate del spec se representará por eventos y estado derivado. La aprobación
no será una variable de proceso ni una pregunta implícita en la conversación.
`resume-run.sh` consultará un `resume-plan` read-only, registrará un único
evento `run_resumed` y relanzará el lead/etapa con el mismo run. El plan deberá
distinguir una etapa abierta a mitad de ejecución de la siguiente etapa aún no
iniciada.

### Controles Codex equivalentes, no hooks falsos

El primer slice verificará precondiciones y postcondiciones desde el runtime:
orden de etapa, gate aprobado, sandbox declarado, árbol de trabajo y eventos
de despacho/finalización. Los controles que dependan de hooks nativos de Claude
se implementarán después como wrappers o checks de Codex; no se declararán
protegidos sólo porque un prompt lo diga.

### Cierre separado del pipeline

La ejecución de agentes termina dejando una rama revisable. Una futura
operación de ship será explícita, humana y separada: revisión del diff,
archivado OpenSpec, merge y limpieza. El pipeline no tendrá credenciales ni
autorización implícita para publicar.

## Risks / Trade-offs

- **[Codex no ofrece exactamente el modelo de subagentes de Claude]** → El
  runtime usará procesos `codex exec` por rol y verificará contratos en los
  puntos de entrada/salida; no fingirá equivalencia de herramientas.
- **[Bash puede ser frágil al manejar JSON]** → Bash compondrá comandos y
  Python validará/transformará JSON; los límites se probarán con casos de
  espacios, errores y procesos muertos.
- **[Un worktree puede quedar sucio tras un proceso muerto]** → La
  reanudación empezará con triage de estado, no declarará éxito por la mera
  existencia del proceso y conservará el run original.
- **[El ledger puede quedar incompleto si muere el proceso]** → Cada transición
  crítica se escribirá de forma durable y el diagnóstico distinguirá ausencia
  de evento de etapa completada.
- **[El repositorio de referencia tiene complejidad y deuda propia]** → Se
  portarán contratos verificables y no todos sus scripts o comportamientos
  históricos; cada bloque tendrá pruebas antes de continuar.

## Migration Plan

1. Implementar y probar paths, worktree y ledger sin lanzar agentes.
2. Añadir el adaptador Codex y ejecutar un `spec-writer` real en un worktree
   temporal.
3. Añadir gate, `resume-plan` y reanudación del mismo run; verificar que no se
   repite `spec-writer`.
4. Añadir `status`, logs, salud e informe sobre el ledger.
5. Recién entonces incorporar las etapas restantes y los guards específicos.

El rollback consiste en cambiar a `main` o a
`backup/pre-reference-rebuild-20260824`; no se requiere restaurar archivos a
mano ni borrar historial.

## Open Questions

- Qué perfil exacto de tmux debe usar el runtime Codex cuando ya exista una
  sesión del proyecto; se puede resolver durante la implementación sin cambiar
  los contratos anteriores.
