## 1. Contrato y entrada

- [x] 1.1 Añadir el prompt específico de `implementer` con change, tasks,
  checkout y restricciones, y verificar que no usa un prompt genérico
- [x] 1.2 Implementar la lectura y validación del handoff de `spec-writer`, y
  verificar que un handoff ausente bloquea antes de lanzar Codex

## 2. Ejecución y evidencia

- [x] 2.1 Persistir el prompt, change, tasks, checkout y archivos modificados,
  y verificar que el resultado queda reconstruible desde el run
- [x] 2.2 Ejecutar la validación estricta posterior y verificar los casos de
  implementación correcta, fallo de Codex y validación fallida

## 3. Integración

- [x] 3.1 Conectar `implementer` al resultado de `spec-writer` dentro del mismo
  run y verificar un handoff completo sin memoria implícita
- [x] 3.2 Ejecutar el pipeline temporal `spec-writer → implementer`, verificar
  que implementer modifica el checkout de prueba y dejar el resultado listo
  para `test-runner`
