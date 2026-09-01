## Purpose

Proporciona reutilización controlada y auditable de contextos de prompt para
reducir trabajo repetido sin mezclar datos entre proyectos o configuraciones.

## ADDED Requirements

### Requirement: La caché de prompts es explícita y aislada

El runtime SHALL permitir configurar la caché en modo `off`, `read-only` o
`read-write`, y cada entrada SHALL quedar aislada por proyecto, rol, modelo,
configuración relevante, versión del contrato y huella del checkout. Sólo se
podrán reutilizar resultados exitosos de roles `read-only`; los roles que
pueden escribir SHALL ejecutar siempre Codex.

#### Scenario: Caché desactivada
- **WHEN** el modo de caché es `off`
- **THEN** la etapa ejecuta Codex y registra `cache_bypass` sin leer ni escribir entradas

#### Scenario: Reutilización válida
- **WHEN** existe una entrada cuya identidad coincide exactamente con la etapa
- **THEN** el runtime reutiliza la entrada y registra `cache_hit` con su identidad

#### Scenario: Identidad modificada
- **WHEN** cambia el prompt, rol, modelo, opciones o versión del contrato
- **THEN** la entrada anterior no se reutiliza y se registra `cache_miss`

#### Scenario: Rol con escritura
- **WHEN** la etapa corresponde a un rol que puede modificar el checkout
- **THEN** el runtime ejecuta Codex y registra `cache_bypass` sin reutilizar resultados

### Requirement: La caché no expone secretos ni rompe la ejecución

El runtime SHALL usar identificadores no reversibles, SHALL aplicar permisos y
límites configurados, y SHALL continuar sin caché si una entrada no puede
leerse, validarse o escribirse.

#### Scenario: Entrada ilegible
- **WHEN** una entrada está corrupta, es incompatible o no puede leerse
- **THEN** el runtime registra `cache_bypass` y ejecuta la etapa normalmente
