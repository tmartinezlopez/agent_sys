## Why

El runtime persiste prompts y logs, pero no tiene una caché de contexto
explícita. Esto puede repetir trabajo y consumo cuando una etapa se reintenta o
se reanuda, y hace difícil distinguir reutilización de una nueva ejecución.

## What Changes

- Añadir una caché opt-in, versionada y limitada por proyecto, rol, modelo y
  configuración relevante.
- Calcular una identidad estable del prompt sin guardar secretos como clave.
- Registrar aciertos, fallos, invalidaciones y bypasses en la evidencia del run.
- Invalidar la entrada cuando cambien el prompt, el contrato del rol o las
  opciones que afectan al resultado.
- Mantener el comportamiento actual cuando la caché está desactivada, es
  ilegible o no está disponible.

## Capabilities

### New Capabilities

- `prompt-cache`: Reutilización segura y observable de contextos de prompt.

### Modified Capabilities

Ninguna. El comportamiento se introduce como una capacidad opt-in adicional.

## Impact

Afecta a `codex-run.py`, la evidencia por etapa, los informes y la configuración
del runtime. No requiere servicios externos ni cambia el contrato de Codex CLI.
