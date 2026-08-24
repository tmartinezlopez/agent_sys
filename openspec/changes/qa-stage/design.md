## Context

`qa` es la última etapa declarada de `STAGES`. Debe cerrar la ejecución usando
los artefactos persistidos, no conversaciones entre procesos. El `ui-reviewer`
puede estar `skipped` cuando no hay cambios de interfaz; ese estado es válido
para permitir que QA continúe.

## Decisions

- Crear un módulo pequeño `qa.py` para construir el prompt, validar el handoff
  y parsear la decisión y los hallazgos.
- Mantener la orquestación en `pipeline.py`, igual que para los roles ya
  implementados.
- Usar `RoleConfig` existente: modelo `gpt-5.4`, razonamiento `medium`,
  sandbox `read-only`, timeout 1200 segundos y un reintento.
- Considerar `passed` solo con proceso exitoso, decisión válida `passed`,
  handoff completo y checkout sin mutaciones.
- Registrar una decisión `blocked` como bloqueo funcional; reservar `failed`
  para errores de ejecución, salida inválida o mutaciones detectadas.
- No ejecutar comandos de reparación ni modificar archivos desde QA.

## Non-goals

- No implementar gates humanos, watchdog, pausa/reanudación ni publicación.
- No añadir un navegador ni una segunda revisión visual.
- No reemplazar la ejecución objetiva de `test-runner`.
- No crear un modelo, rol o formato de salida alternativo.

## Flow

1. El pipeline comprueba los estados y artefactos de las etapas anteriores.
2. QA recibe el objetivo, el checkout y las rutas de evidencia.
3. El lanzador ejecuta `codex exec` con el contrato de solo lectura.
4. El coordinador valida la salida, el código y el estado Git.
5. Se escriben el resumen, el resultado y los eventos de cierre.

