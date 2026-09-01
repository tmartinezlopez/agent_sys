# Backlog del runtime de desarrollo Codex

Este backlog recoge lo necesario para considerar el runtime reutilizable,
usable y pulido en otros repositorios. Las tareas están ordenadas por prioridad
y dependencia. `P0` bloquea el uso normal; `P1` es necesario para una primera
versión reutilizable; `P2` mejora robustez y experiencia; `P3` son extensiones.

## P0 — Bloqueantes para declarar la primera versión usable

- [x] **P0.6 Definir el contrato del coordinador principal.**
  El coordinador es una única instancia Codex con visión global del proyecto,
  responsable de lanzar terminales y agentes, supervisar etapas y decidir los
  gates. Los seis roles son subordinados especializados y no coordinadores.

- [x] **P0.0 Aplicar política de consumo responsable.**
  Las pruebas normales deben usar un Codex falso determinista; las E2E reales
  requieren una activación explícita, un límite de etapas y un presupuesto
  definido. No se deben lanzar agentes reales para validar cambios pequeños del
  runtime. La implementación debe registrar llamadas, duración, modelo,
  reasoning y uso/caché cuando el CLI lo exponga, y bloquear ejecuciones que
  superen el presupuesto.

- [x] **P0.1 Corregir la reanudación desde snapshots.**
  `resume-run.sh` debe resolver el runtime original cuando se ejecuta desde
  `.pipeline/runs/<run_id>/runtime`, usando `PIPELINE_SCRIPT_DIR` igual que
  `run-stage.sh`. La reanudación debe funcionar desde el gate de especificación,
  desde cada etapa posterior, después de un fallo y después de un timeout.

- [x] **P0.2 Recuperar la batería determinista completa.**
  `tests/full-pipeline.sh` y `tests/vertical-slice.sh` deben pasar junto con
  contratos, operaciones read-only, guard de Git y parada segura.

- [x] **P0.3 Añadir una prueba específica de ejecución desde una copia instalada.**
  El runtime debe funcionar cuando `scripts/pipeline` procede de otro checkout
  y los artefactos del run se encuentran en el proyecto destino, sin depender
  accidentalmente del repositorio `agent_sys`.

- [x] **P0.4 Ejecutar la aceptación real no-UI y excluir UI real.**
  El flujo no-UI fue validado con el Codex CLI real. La ruta UI queda cubierta
  por pruebas deterministas y fuera de alcance para la v1; no se ejecutará una
  E2E UI real ni se considerará un bloqueo de release.

- [x] **P0.5 Definir la matriz de compatibilidad.**
  Documentar versiones mínimas y soportadas de Git, Python, Codex CLI, OpenSpec
  y tmux; comprobar que el texto no queda desactualizado respecto al entorno
  real (`openspec/config.yaml` todavía menciona Codex CLI 0.149.1 y el entorno
  actual usa 0.150.1).

## P1 — Primera versión reutilizable en otros proyectos

### Instalación y exportación

- [x] **P1.1 Crear un instalador/bootstrap oficial.**
  Añadir un comando o script que instale `scripts/pipeline`, fusione las
  entradas necesarias del `.gitignore`, compruebe Git/Python/Codex/OpenSpec y
  dé errores accionables. Debe ser idempotente y no sobrescribir configuración
  propia sin confirmación.

- [x] **P1.2 Crear una plantilla de proyecto/runtime.**
  Definir claramente qué se exporta (`scripts/pipeline`), qué es opcional
  (`tests`, `docs`) y qué debe crearse o adaptarse en destino
  (`openspec/config.yaml`, `openspec/specs`). Incluir un ejemplo mínimo.

- [x] **P1.3 Separar configuración del runtime y del proyecto.**
  Evitar que un proyecto consumidor tenga que copiar ciegamente el contexto y
  las especificaciones de `agent_sys`. El runtime debe localizar o validar la
  configuración OpenSpec del checkout destino.

- [x] **P1.4 Hacer configurables las convenciones de paths.**
  Mantener `PIPELINE_WORKTREES_DIR`, pero documentarlo y cubrir también nombre
  del repositorio, ubicación de runs, sesión tmux y posibles worktrees fuera
  del directorio padre. Validar rutas y nombres antes de crear nada.

### Configuración y preflight

- [x] **P1.5 Añadir preflight antes de crear un run.**
  Comprobar repositorio Git válido, rama base, checkout limpio o política
  explícita para cambios locales, OpenSpec disponible, Codex autenticado,
  modelos configurados y permisos de escritura. No crear worktrees ni runs si
  falla el preflight.

- [x] **P1.6 Externalizar `roles.json` sin perder el catálogo seguro.**
  Permitir configuración por proyecto de modelos y timeouts, manteniendo una
  lista cerrada de roles, sandboxes esperados y validación estricta. El error
  de un modelo no disponible debe explicar cómo sustituirlo.

- [ ] **P1.7 Añadir detección explícita de capacidades opcionales.**
  UI-reviewer debe indicar si requiere integración de navegador; tmux debe ser
  opcional; y las funcionalidades no disponibles deben degradar con un error
  claro, no con un bloqueo ambiguo.

### Estados, gates y recuperación

- [ ] **P1.8 Completar el flujo de `changes` y `discard`.**
  Definir qué ocurre después de solicitar cambios en `gate_spec` o `gate_release`:
  reabrir/reintentar la etapa correcta, conservar historial y permitir volver
  a aprobar. `discard` debe dejar el run terminal y explicar si el worktree se
  conserva.

- [ ] **P1.9 Hacer el ledger robusto ante concurrencia y reinicios.**
  Añadir bloqueo de escritura, validación de transiciones, recuperación de
  eventos incompletos y comportamiento definido si dos comandos operan sobre
  el mismo `run_id`.

- [ ] **P1.10 Revisar idempotencia de todas las operaciones.**
  Repetir `gate`, `resume`, `summary`, `stop` y `rebuild` no debe duplicar
  trabajo ni producir estados contradictorios. Añadir pruebas para cada caso.

- [x] **P1.11 Definir retención y limpieza de artefactos.**
  Documentar qué queda en `.pipeline/runs`, añadir una limpieza explícita y
  segura de runs finalizados, y garantizar que nunca elimine worktrees o runs
  activos accidentalmente.

### Operación e integración humana

- [ ] **P1.12 Mejorar la CLI de operación.**
  Unificar ayuda, códigos de salida, mensajes, formato JSON opcional y
  resolución automática de `run_id`/worktree. Los mensajes deben indicar el
  siguiente comando cuando el run queda bloqueado en un gate.

- [x] **P1.13 Documentar el ciclo completo de integración.**
  Explicar inspección, revisión humana, merge, push y limpieza posterior. La
  integración automática seguirá desactivada por seguridad.

- [ ] **P1.14 Decidir si hace falta una operación `ship-feature`.**
  Si se quiere automatizar la integración, diseñar una operación separada con
  confirmación humana, comprobaciones de rama y protección contra publicar por
  accidente. Si no se quiere, registrar formalmente que queda fuera de alcance.

## P2 — Robustez y acabado

### Calidad técnica

- [x] **P2.1 Añadir una verificación única para CI/local.**
  Crear un comando que ejecute `bash -n`, compilación/importación Python,
  tests deterministas y `openspec validate --all --strict`.

- [ ] **P2.2 Añadir linting y análisis estático opcional.**
  Integrar ShellCheck y un checker Python, documentando versiones y excepciones.

- [ ] **P2.3 Eliminar supuestos de plataforma.**
  Evitar rutas absolutas innecesarias como `/usr/bin/git`, detectar binarios de
  forma portable y documentar Bash/POSIX/Linux soportados.

- [ ] **P2.4 Mejorar validación de entradas y seguridad de rutas.**
  Cubrir espacios, unicode, caracteres especiales, symlinks, rutas relativas,
  nombres de branch, `run_id` y worktrees que ya existen. Impedir escapes fuera
  del checkout o del directorio de worktrees configurado.

- [ ] **P2.5 Revisar el guard de Git.**
  Confirmar qué operaciones quedan bloqueadas, qué ocurre con aliases y rutas
  alternativas al binario Git, y dejar claro que el guard no sustituye la
  revisión de permisos del sandbox.

### Observabilidad y soporte

- [ ] **P2.6 Completar el watchdog.**
  `run-health-check.py` debe detectar procesos detenidos, etapas estancadas,
  timeouts y ledger inconsistente con umbrales configurables, sin mutar el
  estado al consultar.

- [ ] **P2.7 Mejorar informes y diagnóstico.**
  Incluir duración, último evento, comando de recuperación, error resumido,
  archivos de evidencia y motivo de bloqueo, sin exponer secretos.

- [ ] **P2.8 Definir tratamiento de secretos y logs.**
  Redactar tokens, variables sensibles y credenciales de la salida persistida;
  documentar permisos de `.pipeline` y política de conservación de logs.

- [ ] **P2.9 Añadir troubleshooting.**
  Cubrir Codex no autenticado, modelo no disponible, OpenSpec ausente, tmux
  ausente, worktree bloqueado, gate pendiente, fallo a mitad de etapa y runs
  antiguos.

### Experiencia de proyecto consumidor

- [x] **P2.10 Añadir README en la raíz o guía de adopción.**
  La guía debe permitir instalar el runtime en un repositorio nuevo sin
  conocer la historia de `agent_sys`.

- [ ] **P2.11 Definir contratos de adaptación por proyecto.**
  Documentar cómo se ejecutan tests, linters, builds, revisión UI y QA del
  proyecto destino; ahora los prompts son genéricos y no conocen sus comandos.

- [ ] **P2.12 Cubrir compatibilidad con repositorios reales.**
  Probar al menos un proyecto Python, uno Node y uno con frontend/UI, con
  worktrees, OpenSpec, comandos de test y configuración propios.

## P3 — Extensiones posteriores

- [ ] **P3.1 Integración opcional con navegador para `ui-reviewer`.**
- [ ] **P3.2 Ejecución paralela sólo donde el contrato lo permita.**
- [ ] **P3.3 Reintentos configurables por etapa y política de backoff.**
- [ ] **P3.4 Exportación/importación de runs y reportes fuera del repositorio.**
- [ ] **P3.5 Adaptador para otros motores de agentes, manteniendo Codex como
  implementación de referencia.**
- [ ] **P3.6 Métricas agregadas de duración, fallos y coste si el CLI las
  proporciona de forma segura.**

## Criterio para declarar `usable y pulido`

Se podrá cerrar este backlog inicial cuando se cumpla todo lo siguiente:

1. Todas las tareas `P0` estén completadas.
2. Exista una instalación documentada y reproducible en un repositorio nuevo.
3. Un flujo no-UI y uno UI completen todas sus etapas con Codex real.
4. Un fallo y un timeout se puedan reanudar sin repetir etapas completadas.
5. Los gates de aprobación, cambios y descarte tengan comportamiento definido y
   probado.
6. El runtime no haga merge, push ni limpieza destructiva automáticamente.
7. La batería de validación local/CI pase desde una copia instalada.
