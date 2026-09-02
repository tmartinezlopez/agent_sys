# Instrucciones para Codex

Este repositorio (`agent_sys`) contiene una metodología reutilizable para
coordinar el desarrollo de otros proyectos. No es la aplicación de negocio.

Cuando el usuario incorpore este repositorio en un proyecto consumidor:

1. Instala la metodología dentro de la raíz del proyecto, en `metodologia/`.
2. Conserva el repositorio Git del proyecto consumidor como repositorio
   principal. No dejes un `.git` anidado dentro de `metodologia/`.
3. Lee `README.md`, `GUIA-USO.md`, `docs/ADOPTION.md` y
   `docs/PROJECT-CONTRACT.md` antes de configurarla.
4. No mezcles los scripts de la metodología con el código de la aplicación.
5. No implementes funcionalidades de negocio durante la instalación.
6. Comprueba los requisitos del proyecto y ejecuta el preflight indicado por
   la documentación.
7. Antes de iniciar trabajo real, informa al usuario de lo configurado, de los
   requisitos pendientes y del comando exacto para iniciar el coordinador.

La metodología debe adaptarse al proyecto mediante su contrato técnico,
comandos de instalación, tests, lint, build, rutas frontend y criterios de QA.
No inventes roles ni modifiques el pipeline sin una petición explícita.

Si el proyecto consumidor ya tiene una carpeta `metodologia/`, no la
sobrescribas sin revisar primero sus cambios y pedir confirmación cuando haya
conflictos.
