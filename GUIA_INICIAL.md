# Guía inicial de `agent_sys`

`agent_sys` será un sistema de agentes construido desde cero, tomando otros proyectos como referencia sin depender de ellos. La prioridad será entender cada pieza, mantener el diseño sencillo y añadir complejidad solo cuando aporte valor.

## Componentes principales

1. **Modelo y proveedor de IA**
   - Cliente para comunicarse con el modelo.
   - Configuración de modelo, temperatura, límites y timeouts.
   - Gestión segura de claves y variables de entorno.

2. **Agente básico**
   - Instrucciones del sistema.
   - Historial de mensajes.
   - Ejecución de una tarea y respuesta estructurada.
   - Control de errores y cancelación.

3. **Herramientas (tools)**
   - Interfaz común para definir herramientas.
   - Validación de argumentos.
   - Registro de llamadas y resultados.
   - Límites de permisos, tiempo y número de llamadas.

4. **Bucle de ejecución**
   - Flujo: pensar/decidir, usar herramientas y responder.
   - Detección de finalización y prevención de bucles infinitos.
   - Límites de tokens, pasos y duración.

5. **Memoria y contexto**
   - Separar contexto temporal de memoria persistente.
   - Controlar qué información se envía al modelo.
   - Evitar almacenar secretos o datos innecesarios.

6. **Orquestación**
   - Ejecución de tareas compuestas.
   - Comunicación entre agentes, si llega a ser necesaria.
   - Estados, reintentos y recuperación ante fallos.

7. **Observabilidad y pruebas**
   - Logs claros y trazas de cada ejecución.
   - Métricas básicas: duración, coste, tokens y errores.
   - Tests unitarios, tests de herramientas y escenarios completos.

8. **Interfaz de uso**
   - Comenzar con una CLI sencilla o una API mínima.
   - Separar la interfaz de la lógica interna para poder cambiarla después.

## Orden recomendado

1. Crear el proyecto, la configuración y un cliente mínimo para el modelo.
2. Implementar un agente que responda sin herramientas.
3. Añadir una única herramienta sencilla y segura.
4. Construir el bucle de ejecución con límites.
5. Incorporar logs y pruebas desde el principio.
6. Añadir memoria, tareas complejas y varios agentes solo cuando exista una necesidad concreta.

## Aspectos importantes

- Mantener interfaces pequeñas y componentes sustituibles.
- No permitir que el modelo ejecute acciones sin permisos explícitos.
- Validar siempre las entradas y salidas de las herramientas.
- Diseñar las operaciones externas para que sean trazables y, cuando sea posible, reversibles.
- Separar configuración, código, datos y secretos.
- Definir el comportamiento ante errores antes de añadir más funcionalidades.
- Documentar las decisiones técnicas y los límites conocidos.
- Priorizar comportamiento determinista, reproducible y fácil de depurar.

La primera versión no debe intentar resolver todos los casos: debe servir para comprender el ciclo completo de una ejecución y convertirse en una base estable para iterar.
