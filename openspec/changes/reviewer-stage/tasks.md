## 1. Contrato y entrada

- [x] 1.1 Añadir el prompt específico de reviewer con handoffs, checklist,
  severidades y decisión, y verificar que es read-only
- [x] 1.2 Validar los handoffs de implementer y test-runner y bloquear sin
  lanzar Codex si falta evidencia

## 2. Revisión y evidencia

- [x] 2.1 Persistir informe estructurado, hallazgos, decisión y estado Git, y
  verificar que un review válido queda reconstruible desde el run
- [x] 2.2 Verificar review aprobado, hallazgo crítico, salida inválida y
  cualquier intento de modificación del checkout

## 3. Integración

- [x] 3.1 Conectar reviewer después de test-runner y hacer que su fallo bloquee
  ui-reviewer y qa
- [x] 3.2 Ejecutar el pipeline temporal hasta reviewer y verificar el handoff
  completo para la siguiente etapa
