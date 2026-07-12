# Quality Checklist: Conversacion Multi-Turno y Reportes PDF

**Purpose**: Validar la CALIDAD DE LOS REQUISITOS del spec 002 antes de `/speckit-plan`.
Esto es un "test unitario del texto": no evalua si el sistema funciona, sino si los
requisitos estan completos, claros, consistentes, medibles y sin contradicciones.

**Created**: 2026-07-12
**Feature**: [spec.md](../spec.md)
**Evaluado contra**: `specs/001-institutional-assistant/spec.md` (FR-001..FR-028) y
`.specify/memory/constitution.md` v1.1.0

**Resultado**: 50 de 57 items cumplidos. 7 requieren correccion (ver seccion Hallazgos).

## Completitud de Requisitos

- [x] CHK001 - Cada historia de usuario (US1..US6) tiene criterios de aceptacion en formato Given/When/Then [Completeness, Spec §User Scenarios]
- [x] CHK002 - Cada historia tiene prioridad asignada (P1/P2/P3) y justificacion de esa prioridad [Completeness, Spec §User Scenarios]
- [x] CHK003 - Cada historia declara un Independent Test verificable de forma aislada [Completeness, Spec §User Scenarios]
- [x] CHK004 - El ciclo de vida completo de la sesion esta especificado: creacion, uso, expiracion y borrado [Completeness, Spec §FR-202, FR-203, FR-204]
- [x] CHK005 - Los cuatro tipos de PDF exigidos estan especificados con su contenido minimo [Completeness, Spec §FR-216..FR-219]
- [x] CHK006 - Estan definidos los datos que cada PDF administrativo debe contener, sin remitir a "lo que haga falta" [Completeness, Spec §FR-216, FR-217, FR-218]
- [ ] CHK007 - No hay requisito que acote cuantas sesiones concurrentes pueden CREARSE. NFR-205 exige soportar 100, pero ningun FR define que pasa al intentar crear la sesion 101, ni si un cliente puede crear sesiones sin limite [Gap, Spec §FR-202, NFR-205]
- [ ] CHK008 - No hay requisitos de observabilidad para la capa de sesion (que se loguea al crear/expirar/borrar una sesion, sin volcar el contenido del historial) [Gap]

## Claridad: Limites de la Memoria Conversacional

- [x] CHK009 - Esta explicito QUE se guarda: turnos completados como par (pregunta, respuesta), incluidos los rechazos por contexto insuficiente [Clarity, Spec §FR-207]
- [x] CHK010 - Esta explicito QUE NO se guarda: los turnos que terminan en error de infraestructura no entran al historial, no consumen cupo y no salen en el PDF [Clarity, Spec §FR-207a]
- [x] CHK011 - Esta explicito CUANTO TIEMPO: TTL configurable, default 30 minutos desde la ultima actividad [Clarity, Spec §FR-204]
- [x] CHK012 - Esta explicito DONDE: solo en memoria de proceso, nunca en disco ni en servicio externo; el reinicio descarta todo [Clarity, Spec §FR-214]
- [x] CHK013 - Los DOS limites distintos estan diferenciados sin ambiguedad: FR-208 acota lo que se ENVIA al pipeline (5 turnos); FR-208a acota lo que se GUARDA por sesion (50 turnos) [Clarity, Spec §FR-208, FR-208a]
- [x] CHK014 - La prohibicion "el historial NO es fuente de conocimiento" esta enunciada como regla estructural verificable, no como intencion: el generador nunca recibe el texto del historial [Clarity, Spec §FR-209, FR-209a, FR-210]
- [x] CHK015 - Esta definido el unico uso permitido del historial (reformular la consulta antes de recuperar) y esta prohibido explicitamente cualquier otro uso [Clarity, Spec §FR-209, §Out of Scope]
- [x] CHK016 - Esta especificado que el rechazo por contexto insuficiente prevalece aunque el historial parezca contener la respuesta [Clarity, Spec §FR-211]

## Consistencia con la Fase 1 (spec 001)

- [x] CHK017 - Las consultas sin `session_id` conservan el comportamiento stateless exacto de la Fase 1: no leen ni escriben historial [Consistency, Spec §FR-201, SC-204]
- [x] CHK018 - La obligacion de citar fuente (FR-005 del spec 001) no se relaja dentro de una sesion [Consistency, Spec §FR-212]
- [x] CHK019 - El texto de rechazo aprobado (FR-007 del spec 001) se reutiliza sin redefinirse [Consistency, Spec §FR-211, §Institutional Source Requirements]
- [x] CHK020 - El corpus sigue acotado a UTN-FRBA Sistemas (FR-028 del spec 001); el feature no agrega fuentes de conocimiento [Consistency, Spec §Contexto, §Institutional Source Requirements]
- [x] CHK021 - La politica de acceso administrativo (FR-026 del spec 001) se reutiliza para los PDF de admin, sin inventar un esquema de auth nuevo [Consistency, Spec §FR-225]
- [x] CHK022 - Los reportes administrativos consumen datos ya definidos por la Fase 1 (FR-011, FR-017, FR-018 del spec 001) sin redefinirlos [Consistency, Spec §Dependencies]
- [x] CHK023 - La convencion de numeracion (serie FR-2xx propia) evita colisiones con FR-001..FR-028 y esta documentada [Consistency, Traceability, Spec §Convencion de numeracion]
- [ ] CHK024 - **CONFLICTO**: el spec 001 sigue declarando en su seccion `Out of Scope` que "Conversation history or multi-turn memory" y "PDF generation or reporting" estan FUERA DE ALCANCE. El spec 002 las implementa. Ningun documento anota que esas dos exclusiones fueron superseded [Conflict, Spec 001 §Out of Scope vs Spec 002 §FR-201, FR-216]

## Consistencia Constitucional (v1.1.0)

- [x] CHK025 - El historial es OPT-IN por sesion y la ausencia de `session_id` mantiene retrocompatibilidad total [Constitution §Estado conversacional OPT-IN, Spec §FR-201]
- [x] CHK026 - Las sesiones son efimeras con TTL configurable, como exige la enmienda [Constitution §Estado conversacional OPT-IN, Spec §FR-204]
- [x] CHK027 - Las respuestas siguen fundadas exclusivamente en el corpus indexado; el Principio IX queda intacto [Constitution §Principio IX, Spec §FR-210, FR-211]
- [x] CHK028 - La persistencia del historial es local y sin servicios externos de pago [Constitution §Stack Tecnologico, Spec §FR-214]
- [x] CHK029 - Los PDF se generan localmente, sin servicios externos [Constitution §Generacion de PDF, Spec §FR-222, SC-208]
- [x] CHK030 - Los parametros operativos (TTL, limites, storage) son configurables centralmente, no hardcodeados [Constitution §Principio IV, Spec §FR-215]
- [x] CHK031 - Todo componente debe trazar a una historia o requisito de este spec [Constitution §Principio I, Spec §FR-226]

## Testeabilidad y Umbrales

- [x] CHK032 - Los NFR de latencia tienen umbral numerico y percentil, no adjetivos ("7 segundos, 95% de las consultas") [Measurability, Spec §NFR-201]
- [x] CHK033 - Los NFR de tamanio de PDF tienen tope numerico explicito (5 MB conversacion / 10 MB administrativo) y tiempo maximo de generacion [Measurability, Spec §NFR-203, NFR-204]
- [x] CHK034 - SC-201 dejo de ser un porcentaje sin referente: define conjunto fijo de 20 pares, umbral 18/20 y metodo de verificacion automatizado [Measurability, Spec §SC-201]
- [x] CHK035 - La garantia anti-contaminacion tiene un criterio verificable por construccion, no por inspeccion manual del texto generado [Measurability, Spec §SC-212]
- [ ] CHK036 - **NFR-202 no es medible**: dice "MUST NOT show measurable latency regression versus Fase 1" sin umbral numerico. "Sin regresion medible" no es un criterio objetivable [Measurability, Ambiguity, Spec §NFR-202]
- [ ] CHK037 - **FR-213 no es objetivable**: "MUST NOT repeat greeting or self-presentation text" no define que constituye un saludo ni como se detecta automaticamente. SC-210 hereda el problema [Measurability, Ambiguity, Spec §FR-213, SC-210]

## Cobertura de Casos Borde: Sesion

- [x] CHK038 - Expiracion por TTL a mitad de conversacion: definida, degrada a stateless e informa, no falla la consulta [Edge Case, Spec §FR-206, §Edge Cases]
- [x] CHK039 - `session_id` inexistente o malformado: definido, error de validacion, sin creacion implicita [Edge Case, Spec §FR-205]
- [x] CHK040 - Limite de historial excedido: los dos limites tienen comportamiento definido (FR-208 descarta del contexto; FR-208a rechaza turnos nuevos sin descartar los guardados) [Edge Case, Spec §FR-208, FR-208a]
- [x] CHK041 - Borrado explicito de sesion: definido, con comportamiento posterior especificado [Edge Case, Spec §FR-203]
- [x] CHK042 - Perdida de sesiones por reinicio del servicio: definida, se trata como sesion expirada, nunca como falla [Edge Case, Spec §FR-214a]
- [x] CHK043 - Concurrencia sobre el mismo `session_id`: definida, se rechaza con error de sesion ocupada [Edge Case, Spec §FR-205a]
- [x] CHK044 - Fallo del paso de reformulacion: definido, degrada a stateless con la pregunta original [Edge Case, Spec §FR-209c]
- [x] CHK045 - Primer turno de una sesion (sin historial previo): definido, no se reformula [Edge Case, Spec §FR-209b]

## Cobertura de Casos Borde: PDF

- [x] CHK046 - Exportar una conversacion con turnos de rechazo: definido, el rechazo se imprime tal cual, sin fuentes fabricadas [Edge Case, Spec §FR-220, SC-209]
- [x] CHK047 - Exportar una consulta stateless: definido, no es exportable, error claro [Edge Case, Spec §FR-224]
- [x] CHK048 - Exportar una sesion expirada, borrada o perdida: definido, error "conversacion no disponible", nunca PDF parcial [Edge Case, Spec §FR-224a]
- [x] CHK049 - Reporte de una corrida de indexacion con cero documentos indexados: definido, el PDF se genera e informa el resultado vacio [Edge Case, Spec §Edge Cases]
- [x] CHK050 - Sujeto de reporte inexistente: definido, error claro en lugar de PDF vacio [Edge Case, Spec §FR-223]
- [x] CHK051 - Conversacion larga o con muchas fuentes: definido, se pagina y no se truncan turnos ni fuentes [Edge Case, Spec §Edge Cases]
- [ ] CHK052 - **GAP: caracteres especiales del espanol**. Ningun requisito cubre el rendering de tildes, `n` con virgulilla, dieresis ni signos de apertura `¿` `¡` en los PDF. Es un modo de falla clasico de las librerias de PDF (fuente sin glifo -> caracteres corruptos o cuadraditos), y todo el contenido de este sistema es espanol argentino [Gap, Spec §FR-221, NFR-203]
- [ ] CHK053 - **GAP: indice vacio o inexistente**. El edge case cubre "corrida con cero documentos", pero no que se pida el PDF de estado del indice (FR-216) cuando todavia no se construyo ningun indice [Gap, Spec §FR-216]

## Dependencias y Supuestos

- [x] CHK054 - Los supuestos estan documentados con su justificacion y su costo aceptado, no como afirmaciones sueltas [Assumption, Spec §Assumptions]
- [x] CHK055 - Las consecuencias de alcance de cada decision estan explicitas (ej: stateless no es exportable; un reinicio pierde conversaciones no exportadas) [Assumption, Spec §Assumptions]
- [x] CHK056 - La dependencia de la Fase 1 operativa y de la enmienda constitucional v1.1.0 esta declarada [Dependency, Spec §Dependencies]
- [x] CHK057 - El supuesto de sesiones anonimas (quien tiene el `session_id` accede al historial) esta explicitado junto con su justificacion de riesgo [Assumption, Spec §Assumptions]

## Hallazgos que Requieren Correccion

Siete items sin cumplir. Ordenados por impacto:

### 1. CHK024 - Conflicto documental con el spec 001 (ALTO)

El spec 001 sigue diciendo, en su seccion `Out of Scope`:

> - Conversation history or multi-turn memory.
> - PDF generation or reporting.

El spec 002 implementa exactamente esas dos cosas. Un reviewer que lea el spec 001 de
forma aislada concluira que la Fase 2 viola el alcance acordado.

**Correccion**: anotar ambas lineas en el spec 001 como superseded, por ejemplo
`[Superseded por spec 002, 2026-07-12]`, sin borrarlas (preservan la historia de la
decision). No requiere tocar el spec 002.

### 2. CHK052 - Caracteres especiales del espanol en los PDF (ALTO)

Todo el corpus, las respuestas y los PDF estan en espanol argentino, pero ningun
requisito exige que los PDF rendericen correctamente tildes, la letra n con virgulilla,
dieresis y los signos de apertura de interrogacion y exclamacion. Es la falla mas comun
al generar PDF con fuentes que no traen los glifos: el documento sale con caracteres
corruptos. Sin requisito, nadie lo va a testear.

**Correccion**: agregar un FR de la serie PDF, del tipo: "Los PDF MUST renderizar
correctamente el repertorio completo de caracteres del espanol (tildes, n con virgulilla,
dieresis, signos de apertura). Un caracter no renderizable MUST fallar la generacion con
error claro, nunca producir un PDF con glifos corruptos." Y un SC que lo verifique con un
texto de prueba que incluya todos esos caracteres.

### 3. CHK036 - NFR-202 no tiene umbral numerico (MEDIO)

"MUST NOT show measurable latency regression versus Fase 1" no es objetivable: no dice
contra que baseline ni con que tolerancia. El pedido explicito era "no 'rapido' sino
'menos de X segundos'".

**Correccion**: cuantificar, por ejemplo: "La latencia p95 de una consulta sin
`session_id` MUST mantenerse dentro del 5% de la baseline de la Fase 1 (SC-004 del spec
001: 5 segundos)."

### 4. CHK037 - FR-213 (saludo) no es automatizable (MEDIO)

"MUST NOT repeat greeting or self-presentation text" no define que cuenta como saludo ni
como detectarlo. SC-210 promete medir el 100% de las conversaciones de prueba, pero sin
una definicion operativa no hay test automatizable.

**Correccion**: definir el criterio de forma objetivable. La opcion mas simple y testeable
es invertir la regla: el asistente NUNCA emite saludo ni presentacion (ni siquiera en el
primer turno), con lo cual el test es una asercion de ausencia contra una lista de
patrones. Si se quiere conservar el saludo en el primer turno, hay que enumerar los
patrones que cuentan como saludo.

### 5. CHK007 - Sin tope de sesiones concurrentes creables (MEDIO)

NFR-205 exige soportar 100 sesiones concurrentes, pero ningun FR dice que ocurre al
intentar crear la 101, ni impide que un cliente cree sesiones sin limite. Con historial en
memoria, esto es un camino directo a agotar RAM. El tope por sesion (FR-208a) acota una
sesion, no la cantidad de sesiones.

**Correccion**: agregar un FR con tope configurable de sesiones activas simultaneas y
comportamiento definido al alcanzarlo (rechazo con error claro, o desalojo de la sesion
mas antigua ya vencida).

### 6. CHK053 - PDF de estado de indice cuando no hay indice (BAJO)

FR-223 cubre "sujeto de reporte inexistente" de forma generica, y el edge case cubre la
corrida con cero documentos. Pero el caso de pedir el PDF de estado del indice cuando
todavia no se construyo ningun indice no esta enunciado.

**Correccion**: o bien explicitar que FR-223 lo cubre, o agregar el edge case: el PDF se
genera informando "indice no construido", en linea con como la Fase 1 ya maneja el indice
no listo.

### 7. CHK008 - Sin requisitos de observabilidad de sesion (BAJO, opcional)

No hay requisitos sobre que se loguea en el ciclo de vida de la sesion. Dado que
"Analytics sobre el historial" esta explicitamente fuera de alcance, la ausencia puede ser
deliberada. Vale la pena una decision explicita: loguear eventos de sesion
(creada/expirada/borrada) SIN volcar el contenido del historial, para poder operar el
sistema sin violar el limite de no-analytics.

## Notas

- Este checklist evalua la CALIDAD DE LOS REQUISITOS, no la implementacion.
- Ninguna correccion aplicada: `spec.md` no fue modificado, segun lo pedido.
- Los items CHK036, CHK037, CHK052 y CHK007 conviene resolverlos ANTES de `/speckit-plan`:
  los cuatro cambian requisitos, no solo redaccion.
- CHK024 se corrige en el spec 001, no en el 002.
