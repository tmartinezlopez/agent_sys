## 1. Contrato persistente

- [x] 1.1 Añadir estados, validaciones y escritura del gate `spec-review`.
- [x] 1.2 Registrar decisión, operador, motivo y eventos sin permitir cambios
      de una decisión ya tomada.

## 2. Coordinador y CLI

- [x] 2.1 Detener el pipeline tras `spec-writer` cuando el gate esté pendiente.
- [x] 2.2 Añadir la orden CLI para aprobar o rechazar un gate por `run_id`.
- [x] 2.3 Reanudar un run aprobado desde `implementer` sin repetir etapas.
- [x] 2.4 Bloquear las etapas restantes cuando el gate sea rechazado.

## 3. Verificación y documentación

- [x] 3.1 Probar pausa, persistencia y ausencia de lanzamiento de implementer.
- [x] 3.2 Probar aprobación, reanudación y conservación del `run_id`.
- [x] 3.3 Probar rechazo, decisiones duplicadas y run desconocido.
- [x] 3.4 Ejecutar la suite, validar OpenSpec y actualizar backlog y arquitectura.
