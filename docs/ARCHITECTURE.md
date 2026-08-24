# Arquitectura de `agent_sys`

## Objetivo

`agent_sys` adapta el patrón de `rburgosm/agentic-system` a procesos externos
de Codex CLI. El operador sigue usando una sesión interactiva de Codex; el
coordinador ejecuta el pipeline y cada rol trabaja con un contrato explícito.

## Flujo completo

```text
operador
  ↓ inicia un objetivo
coordinador Bash/Python
  ↓ crea run_id y carga el pipeline
estado y eventos persistentes
  ↓ preparan la evidencia del run
tmux: sesión del proyecto
  ├── coordinator
  └── ventanas nombradas por etapa
        ↓
procesos externos `codex exec`
  ↓ escriben logs y artefactos
coordinador evalúa estado, gates y avance
```

El operador decide iniciar, aprobar gates, reintentar, pausar o detener. El
coordinador no depende de memoria conversacional: cada etapa recibe un prompt,
un directorio, una configuración y rutas de artefactos explícitas.

## Roles y orden

| Orden | Rol | Modelo | Reasoning | Sandbox |
|---:|---|---|---|---|
| 1 | `spec-writer` | `gpt-5.6-luna` | `medium` | `workspace-write` |
| 2 | `implementer` | `gpt-5.4` | `medium` | `workspace-write` |
| 3 | `test-runner` | `gpt-5.3-codex` | `medium` | `read-only` |
| 4 | `reviewer` | `gpt-5.6-luna` | `medium` | `read-only` |
| 5 | `ui-reviewer` | `gpt-5.4` | `medium` | `read-only` |
| 6 | `qa` | `gpt-5.4` | `medium` | `read-only` |

`ui-reviewer` solo se ejecuta cuando el change afecta a la interfaz. Los roles
son procesos independientes de Codex y no comparten memoria implícita.

## Capas

### Operador

Arranca el coordinador desde su Codex interactivo y decide sobre gates y
paradas. No necesita conocer los índices internos de tmux.

### Coordinador

Recibe el objetivo, genera `run_id`, carga la configuración de roles, prepara
el run, lanza etapas, registra eventos y decide si la siguiente etapa está
permitida.

### Estado y artefactos

Cada run tendrá esta estructura:

```text
runs/<run_id>/
├── run.json
├── events.jsonl
├── summary.json
└── stages/<stage_id>/
    ├── prompt.md
    ├── stdout.log
    ├── stderr.log
    ├── result.json
    └── artefactos del rol
```

Estados de etapa y run:

```text
pending → running → passed
                    ├→ failed
                    └→ blocked
```

Una etapa no avanza si la anterior no está `passed` o si falta un gate humano
obligatorio. Después de `spec-writer`, el gate `spec-review` queda pendiente y
el operador debe aprobarlo o rechazarlo desde la CLI. Una aprobación reanuda el
mismo `run_id` desde `implementer`; un rechazo bloquea las etapas restantes.
`ui-reviewer` puede quedar `skipped` cuando el cambio no afecta a la interfaz;
si sí afecta y no existe bridge de navegador, queda bloqueado. `qa` es la
última etapa: necesita la evidencia completa y solo aprueba con una decisión
estructurada y el checkout sin mutaciones.

Ejemplo de decisión del operador:

```bash
PYTHONPATH=src python3 -m agent_sys.cli --gate spec-review \
  --run-id <run_id> --decision approve --operator tomas
```

### Tmux

La sesión pertenece al proyecto y las ventanas se identifican por nombre, no
por índice:

```text
<proyecto>
├── coordinator
└── run:<run_id>:<role>
```

El coordinador verifica que la sesión y la ventana son suyas antes de observar,
renombrar o detener procesos. Nunca mata sesiones ajenas ni usa comandos
globales como `tmux kill-server`, `pkill` o `killall`.

### Agentes Codex

Cada proceso se lanza con `codex exec` y recibe explícitamente:

```text
rol
modelo
reasoning
sandbox
directorio de trabajo
prompt contractual
timeout
rutas de salida
```

La salida, el código de salida y los errores se persisten antes de decidir el
avance. No se utiliza la API de OpenAI.

## Adaptación de Roberto a Codex

Roberto separa los contratos de rol (`.claude/agents/`) del runtime
(`scripts/pipeline/`) y delega en subagentes nativos de Claude. Aquí se conserva
esa separación, pero cada rol es un proceso externo de Codex lanzado por el
coordinador y visible en tmux.

## Prerrequisitos actuales

- OpenSpec `1.10.0`, inicializado para Codex.
- Codex CLI `0.149.1`, autenticado mediante ChatGPT.
- tmux `3.6`.
- El directorio actual ya es un checkout Git local con `origin/main` conservado;
  no se ha hecho push y los worktrees siguen fuera del alcance de este bloque.
