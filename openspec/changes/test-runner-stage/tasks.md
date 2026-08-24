## 1. Contrato y entrada

- [x] 1.1 Añadir el prompt específico de `test-runner` con handoff,
  checkout, comando de pruebas y salida esperada, y verificar que es read-only
- [x] 1.2 Validar el handoff de `implementer` y bloquear sin lanzar Codex si
  falta o no está pasado

## 2. Ejecución y evidencia

- [x] 2.1 Configurar y ejecutar `PYTHONPATH=src pytest -q`, persistiendo
  comando, stdout, stderr, código y resumen verificable
- [x] 2.2 Verificar pruebas correctas, fallidas y timeout, y que no se modifica
  el checkout desde test-runner

## 3. Integración

- [x] 3.1 Conectar `test-runner` al mismo run después de implementer y dejar la
  evidencia disponible para reviewer
- [x] 3.2 Ejecutar el pipeline temporal `spec-writer → implementer → test-runner`
  y verificar que un fallo de pruebas detiene las etapas posteriores
