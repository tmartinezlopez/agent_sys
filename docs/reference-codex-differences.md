# Referencia operativa de la metodología

Este documento describe cómo debe entender y utilizar Codex esta metodología.
La copia maestra se mantiene fuera de los proyectos consumidores; cada
proyecto conserva su propia copia en `metodologia/` y la actualiza desde la
ruta local configurada por el operador.

## Qué se conserva

- worktree y rama `feature/<item>` por funcionalidad;
- ledger append-only por ejecución;
- gates humanos;
- reanudación mediante el mismo `run_id`;
- consultas de estado y evidencias por etapa;
- integración final bajo decisión humana.

## Quién coordina

El coordinador es el Codex principal del proyecto. Es una única instancia con
visión global y responsabilidad sobre todo el trabajo: interpreta el objetivo,
planifica, lanza y controla terminales/agentes, asigna etapas, revisa
resultados, decide reintentos y solicita las decisiones humanas de los gates.

La carpeta `metodologia/` no crea un coordinador nuevo por funcionalidad. Sus
scripts son herramientas que utiliza ese coordinador.

## Agentes subordinados

Los agentes `spec-writer`, `implementer`, `test-runner`, `reviewer`,
`ui-reviewer` y `qa` son roles especializados. Ejecutan únicamente la etapa
que les asigna el coordinador y no tienen responsabilidad de coordinación
global ni deben lanzar otros agentes.

## Adaptación a Codex

Los agentes y mecanismos específicos de Claude se sustituyen por procesos
externos `codex exec`, con los seis roles declarados en `roles.json`, usando
`--dangerously-bypass-approvals-and-sandbox` para evitar interrupciones de
permisos durante el trabajo. El runtime
proporciona worktrees, ledger, prompts por etapa, evidencias, gates y
reanudación; no hace merge, push ni publicación automática.

La secuencia no-UI es:

```text
coordinador → spec-writer → gate_spec → implementer → test-runner → reviewer → qa → gate_release
```

La revisión UI determinista está disponible. La E2E UI real queda fuera de la
versión actual.

## Limitaciones conocidas

- No existe todavía una operación automática de `ship-feature`.
- No hay caché explícita de prompts ni contador de tokens del modelo; sí hay
  reanudación sin repetir etapas completadas y límite de despachos.
- El coordinador principal debe leer `GUIA-USO.md` antes de operar la
  metodología.
