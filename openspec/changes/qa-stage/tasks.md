## 1. Contrato y handoff

- [x] 1.1 Añadir el contrato de salida y parser de decisiones de `qa`.
- [x] 1.2 Validar que todas las etapas anteriores tienen estado y artefactos
      compatibles, aceptando `ui-reviewer=skipped` únicamente cuando corresponda.

## 2. Ejecución real

- [x] 2.1 Construir el prompt específico de QA con objetivo y evidencias.
- [x] 2.2 Integrar QA en `pipeline.py` usando `codex exec` y configuración real.
- [x] 2.3 Persistir `qa-summary.json`, `result.json`, logs y eventos.
- [x] 2.4 Detectar timeout, proceso fallido, salida inválida y mutaciones del
      checkout sin marcar QA como aprobado.

## 3. Verificación

- [x] 3.1 Probar aprobación con decisión estructurada y evidencia completa.
- [x] 3.2 Probar bloqueo por predecesor no aprobado.
- [x] 3.3 Probar decisión bloqueada, salida inválida y timeout.
- [x] 3.4 Probar que una mutación del checkout impide el aprobado.
- [x] 3.5 Ejecutar toda la suite, validar OpenSpec y actualizar backlog y
      arquitectura.
