## 1. Detección y contrato

- [ ] 1.1 Detectar si el change afecta UI y verificar skip explícito para
  cambios no visuales
- [ ] 1.2 Añadir prompt y configuración de navegador/URL sin crear valores
  ficticios, y verificar que la etapa es read-only

## 2. Capacidad visual

- [ ] 2.1 Implementar comprobación de bridge real y servidor dev, y verificar
  `NO_VERIFICABLE` cuando cualquiera falte
- [ ] 2.2 Persistir escenarios, evidencia visual, consola, pestañas creadas y
  veredicto; verificar que no se tocan pestañas ni checkout ajenos

## 3. Integración

- [ ] 3.1 Conectar la etapa como condicional después de reviewer y antes de QA,
  sin bloquear cambios que no afecten UI
- [ ] 3.2 Probar un cambio no visual y un cambio visual sin bridge, verificando
  skip y `blocked` respectivamente; dejar preparado el contrato para un MCP
  real futuro
