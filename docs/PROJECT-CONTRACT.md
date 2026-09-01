# Contrato de adaptación por proyecto

La metodología aporta la coordinación y la mecánica del pipeline. El proyecto
consumidor debe aportar su realidad técnica.

## El proyecto debe definir

- comandos de instalación, tests, lint y build;
- qué rutas contienen frontend y qué requiere una revisión UI;
- criterios de QA y datos de prueba seguros;
- convenciones de rama, backlog y OpenSpec;
- servicios o credenciales necesarias para una ejecución real.

## Recomendación

Registrar estas decisiones en la documentación del proyecto o en un archivo
de configuración propio. No modificar `roles.json` para inventar roles: la
lista de roles es cerrada y sólo deben adaptarse comandos, rutas, modelos o
timeouts permitidos por el runtime.

Antes de ejecutar una feature, comprobar:

```bash
metodologia/scripts/pipeline/preflight.sh --worktree "$PWD"
metodologia/scripts/pipeline/project-backlog.sh --worktree "$PWD"
```

Si no existe backlog, el coordinador debe indicarlo explícitamente. Las
pruebas del runtime usan un agente falso; Codex real sólo se activa durante una
ejecución manual y limitada.
