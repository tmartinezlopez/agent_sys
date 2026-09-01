## 1. Normalización

- [x] 1.1 Definir el esquema de uso y estados `reported`/`unknown`, y verificarlo con salidas Codex completas y parciales
- [x] 1.2 Implementar el parser tolerante y conservar versión/origen, verificando compatibilidad cuando falten campos

## 2. Presupuesto y consultas

- [x] 2.1 Integrar métricas en ledger, informes y diagnóstico, y verificar acumulados sin duplicación al reanudar
- [x] 2.2 Implementar presupuesto por run y bloqueo previo al despacho, verificando límite superado y desactivado
- [x] 2.3 Añadir pruebas de regresión y ejecutar `bash tests/check-all.sh` y `openspec validate --all --strict`
