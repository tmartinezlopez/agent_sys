## 1. Contrato y prompt del rol

- [x] 1.1 Añadir el prompt contractual real de `spec-writer` con objetivo,
  nombre de change, comandos OpenSpec permitidos y artefactos esperados, y
  verificarlo con un test que compruebe que no usa un rol genérico
- [x] 1.2 Añadir la configuración de salida del rol al catálogo y verificar que
  conserva `gpt-5.6-luna`, `medium`, `workspace-write` y los artefactos requeridos

## 2. Validación del handoff

- [x] 2.1 Implementar la comprobación del nombre del change y de proposal,
  specs, design y tasks, y verificar que un artefacto ausente impide `passed`
- [x] 2.2 Ejecutar `openspec validate <change> --strict`, persistir comando,
  salida y código, y verificar casos de validación correcta y fallida

## 3. Integración del pipeline

- [x] 3.1 Conectar la evaluación específica de `spec-writer` al resultado de la
  etapa y verificar un handoff completo reconstruible desde `run.json`
- [x] 3.2 Ejecutar el primer pipeline real con un change OpenSpec temporal,
  conservar todos sus artefactos y verificar que el resultado queda listo para
  `implementer`
