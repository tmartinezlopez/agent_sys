## 1. Identidad y almacenamiento

- [x] 1.1 Definir el formato versionado de entrada y la clave hash, limitada a resultados read-only y huella del checkout, y verificar colisiones y aislamiento con pruebas deterministas
- [x] 1.2 Implementar modos `off`, `read-only` y `read-write`, con permisos y límites, y verificar su configuración inválida

## 2. Integración y seguridad

- [x] 2.1 Integrar lectura/escritura en el despacho de etapas sin alterar el ledger, y verificar hit, miss y bypass
- [x] 2.2 Añadir redacción de secretos, invalidación y limpieza segura, y verificar que no se modifican runs ni worktrees
- [x] 2.3 Añadir la decisión de caché a logs e informes y verificar `bash tests/check-all.sh`
