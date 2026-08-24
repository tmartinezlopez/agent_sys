## Context

La referencia usa `mcp__claude-in-chrome__*` para seleccionar un navegador,
crear una pestaña, navegar, capturar evidencia y cerrar solo las pestañas
creadas. En este entorno `codex mcp list` no muestra servidores configurados y
el repositorio no declara servidor web ni frontend.

## Goals / Non-Goals

**Goals:**

- Mantener la etapa en el pipeline sin falsear su resultado.
- Detectar alcance UI y registrar cuándo se omite.
- Poder activar una revisión real cuando se configure un bridge compatible.

**Non-Goals:**

- Crear un navegador falso, screenshots sintéticas o un servidor web genérico.
- Añadir ahora una dependencia externa de navegador sin decisión operativa.
- Revisar lógica de servidor, responsabilidad del reviewer.

## Decisions

- La disponibilidad del navegador será una precondición explícita, no una
  suposición del prompt.
- La falta de bridge o servidor produce `NO_VERIFICABLE`/`blocked`, nunca
  `passed`.
- El stage recibirá la URL base y comando de desarrollo desde configuración
  del proyecto cuando existan; no inventará puertos.
- Se conservará aislamiento: perfil dedicado si existe, pestaña nueva y cierre
  únicamente de pestañas creadas por la etapa.

## Risks / Trade-offs

- [Risk] Sin MCP la etapa no puede validar visualmente → Mitigation: estado
  explícito no verificable y gate humano o configuración posterior.
- [Risk] Un navegador principal puede ser del operador → Mitigation: preferir
  perfil dedicado y no redimensionar ni cerrar pestañas ajenas.
- [Risk] El servidor puede no estar disponible → Mitigation: comprobar URL y
  detener sin arrancar procesos de larga duración automáticamente.
