# Feature Specification: Conversacion Multi-Turno y Reportes PDF

**Feature Branch**: `[002-conversacion-y-reportes]`

**Created**: 2026-07-12

**Status**: Draft

**Input**: User description: "Fase 2 del Asistente Institucional UTN: agregar historial de conversacion / memoria multi-turno y generacion de reportes en PDF. La Fase 1 (001-institutional-assistant) queda intacta; este feature la extiende."

## Contexto y Relacion con la Fase 1

Este feature EXTIENDE `specs/001-institutional-assistant`. Las capacidades de la
Fase 1 NO se re-especifican aca; se referencian:

- Pipeline RAG local, corpus acotado a UTN-FRBA / Ingenieria en Sistemas (FR-028 del spec 001).
- Toda respuesta fundada en contenido recuperado incluye URL de fuente obligatoria (FR-005 del spec 001, revisado 2026-07-10).
- Rechazo por contexto insuficiente con el texto aprobado (FR-007 del spec 001).
- Consulta sin `session_id` = comportamiento identico a Fase 1 (stateless).

Habilitado por la enmienda constitucional v1.1.0 (Restricciones de Arquitectura:
"Estado conversacional OPT-IN por sesion" y "Generacion de PDF").

### Convencion de numeracion

Este feature ABRE SERIE PROPIA en lugar de continuar la numeracion del spec 001
(que termina en FR-028). Motivo: los dos specs deben poder editarse y versionarse
de forma independiente sin colisiones de identificadores.

| Serie | Uso |
|-------|-----|
| `FR-2xx` | Requisitos funcionales de este feature |
| `NFR-2xx` | Requisitos no funcionales de este feature |
| `SC-2xx` | Criterios de exito de este feature |

Las referencias a requisitos de la Fase 1 se escriben siempre como
"FR-0xx del spec 001" para evitar ambiguedad.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Conversacion con referencias a turnos anteriores (Priority: P1)

Como estudiante, quiero hacer una pregunta de seguimiento que se apoye en lo que
ya pregunte ("y como es el tramite?"), para no tener que repetir el tema completo
en cada consulta.

**Why this priority**: Es el nucleo de la Fase 2. Sin esto, el resto del feature
de conversacion no entrega valor.

**Independent Test**: Abrir una sesion, preguntar por equivalencias, luego
preguntar "y como es el tramite?" y verificar que la respuesta trate sobre el
tramite de equivalencias y cite fuente institucional del corpus.

**Acceptance Scenarios**:

1. **Given** una sesion activa donde el usuario ya pregunto "como funcionan las equivalencias?", **When** pregunta "y como es el tramite?", **Then** el asistente interpreta la consulta como referida a equivalencias y responde con contenido recuperado del corpus, citando fuente.
2. **Given** una sesion activa, **When** el usuario envia el primer turno, **Then** la respuesta es equivalente en calidad y formato a una respuesta stateless de la Fase 1.
3. **Given** una consulta de seguimiento cuyo tema NO tiene respaldo en el corpus indexado, **When** el asistente evalua el contexto recuperado, **Then** responde con el texto de rechazo aprobado (FR-007 del spec 001) aunque el historial contenga informacion aparentemente relacionada.
4. **Given** una consulta enviada SIN `session_id`, **When** el sistema la procesa, **Then** se comporta exactamente como en la Fase 1: no lee ni escribe historial.

---

### User Story 2 - Ciclo de vida de la sesion (Priority: P1)

Como usuario, quiero que mi conversacion tenga un inicio y un final claros y
pueda borrarla cuando quiera, para controlar que contexto conserva el asistente.

**Why this priority**: Sin creacion, expiracion y borrado de sesion, el historial
no es operable ni auditable, y el limite constitucional de efimeridad no es
verificable.

**Independent Test**: Crear una sesion, usarla, borrarla explicitamente y
verificar que un turno posterior con ese `session_id` ya no accede al historial
previo.

**Acceptance Scenarios**:

1. **Given** que el usuario quiere conversar, **When** solicita iniciar una sesion, **Then** el sistema devuelve un `session_id` unico.
2. **Given** una sesion activa, **When** el usuario solicita borrarla, **Then** el historial se elimina y una consulta posterior con ese `session_id` se trata como sesion inexistente.
3. **Given** una sesion cuyo TTL configurado ya vencio, **When** el usuario envia un nuevo turno con ese `session_id`, **Then** el sistema responde la consulta como stateless e informa que la sesion expiro.
4. **Given** un `session_id` con formato invalido o inexistente, **When** el usuario envia una consulta, **Then** el sistema devuelve un error de validacion claro y no crea la sesion implicitamente.

---

### User Story 3 - El historial no contamina la respuesta (Priority: P1)

Como responsable institucional, quiero garantia de que el asistente nunca
responde con informacion que provenga del historial en vez del corpus, para que
las respuestas sigan siendo trazables a una fuente oficial.

**Why this priority**: Es el limite constitucional duro del Principio IX y de la
enmienda v1.1.0. Si se rompe, el feature no puede desplegarse.

**Independent Test**: En una sesion, hacer que el usuario afirme un dato falso
("me dijeron que la inscripcion cierra el 30"), luego preguntar por esa fecha, y
verificar que el asistente NO repita el dato del usuario como si fuera
institucional.

**Acceptance Scenarios**:

1. **Given** que el usuario afirmo un dato en un turno previo, **When** pregunta por ese dato y el corpus no lo respalda, **Then** el asistente responde con el texto de rechazo aprobado y NO repite la afirmacion del usuario como informacion institucional.
2. **Given** que el asistente responde en un turno de una sesion, **When** la respuesta se basa en contenido recuperado, **Then** incluye al menos una URL de fuente, igual que en la Fase 1.
3. **Given** cualquier turno de una sesion, **When** se inspecciona la respuesta, **Then** toda afirmacion institucional es trazable a un fragmento recuperado del corpus en ese turno, no al historial.

---

### User Story 4 - Saludo no repetido (Priority: P3)

Como usuario, quiero que el asistente no me salude ni se presente en cada turno,
para que la conversacion se sienta continua y no repetitiva.

**Why this priority**: Es calidad de experiencia, no correctitud. La conversacion
funciona sin esto.

**Independent Test**: Enviar tres turnos en una misma sesion y verificar que el
saludo/presentacion aparece a lo sumo en el primero.

**Acceptance Scenarios**:

1. **Given** una sesion con al menos un turno previo, **When** el asistente responde el segundo turno, **Then** la respuesta no incluye saludo ni presentacion.
2. **Given** una consulta stateless o el primer turno de una sesion, **When** el asistente responde, **Then** el saludo/presentacion es admisible.

---

### User Story 5 - Reportes PDF de administracion (Priority: P2)

Como administrador, quiero exportar en PDF el estado del indice, el resumen de
una corrida de indexacion y el listado de fuentes configuradas, para archivar y
compartir evidencia del estado del sistema.

**Why this priority**: Entrega valor operativo real y es independiente de la
conversacion, pero el sistema ya es util sin esto.

**Independent Test**: Con un indice construido, exportar cada uno de los tres
reportes y verificar que el PDF abre correctamente y contiene los datos que
muestra la vista equivalente de la Fase 1.

**Acceptance Scenarios**:

1. **Given** un indice construido, **When** el administrador exporta el estado del indice en PDF, **Then** el PDF contiene cantidad de documentos, fecha de ultima actualizacion exitosa, areas cubiertas y fallos recientes.
2. **Given** una corrida de indexacion finalizada, **When** el administrador exporta su resumen en PDF, **Then** el PDF contiene modo de actualizacion, tiempos, cantidad de documentos indexados y fallidos, y el detalle de fuentes fallidas.
3. **Given** fuentes configuradas, **When** el administrador exporta el reporte de fuentes, **Then** el PDF lista cada fuente con URL, area, regional/departamento, tipo y estado activo.
4. **Given** cualquier exportacion, **When** el PDF se genera, **Then** incluye fecha de generacion e identificacion del sistema, y se produce sin llamar a ningun servicio externo.
5. **Given** que no existe la corrida de indexacion solicitada, **When** el administrador pide su PDF, **Then** el sistema devuelve un error claro y no genera un PDF vacio.

---

### User Story 6 - Exportar la conversacion en PDF (Priority: P2)

Como estudiante, quiero exportar en PDF la conversacion que tuve con el
asistente, con todas sus preguntas, respuestas y fuentes citadas, para guardarla,
imprimirla o presentarla en una gestion administrativa.

**Why this priority**: Convierte una conversacion efimera en un documento util
para tramites, pero depende de que el flujo de conversacion ya funcione.

**Independent Test**: Mantener una conversacion de varios turnos, exportarla en
PDF y verificar que el PDF contiene todos los turnos en orden, con sus fuentes
citadas.

**Acceptance Scenarios**:

1. **Given** una sesion con varios turnos respondidos, **When** el usuario exporta la conversacion en PDF, **Then** el PDF contiene todos los turnos en orden, cada uno con la pregunta, la respuesta y las URLs de fuente con titulo cuando exista, mas la fecha de generacion.
2. **Given** una conversacion que incluye un turno de rechazo por contexto insuficiente, **When** el usuario la exporta, **Then** ese turno aparece indicando explicitamente que el asistente no tenia informacion suficiente, sin fuentes inventadas.
3. **Given** una consulta stateless (sin `session_id`), **When** el usuario intenta exportarla, **Then** el sistema devuelve un error claro indicando que exportar requiere una sesion, y no genera un PDF.
4. **Given** una sesion expirada, borrada o perdida por reinicio del servicio, **When** el usuario intenta exportarla, **Then** el sistema informa que la conversacion ya no esta disponible y no genera un PDF parcial.
5. **Given** una conversacion exportada, **When** se compara con lo que el asistente respondio, **Then** el contenido del PDF proviene del historial registrado por el sistema, no de contenido enviado por el cliente.

### Edge Cases

- **Sesion expirada a mitad de conversacion**: el turno se responde como stateless (sin historial) y la respuesta informa que la sesion expiro. El sistema NO reconstruye silenciosamente el historial perdido ni falla la consulta.
- **`session_id` invalido o inexistente**: error de validacion claro; el sistema no crea la sesion implicitamente ni responde como si la sesion existiera.
- **Historial que excede el limite configurado**: se incluyen solo los turnos mas recientes dentro del limite; los mas antiguos se descartan del contexto enviado. El descarte NUNCA provoca un error ni degrada la obligacion de citar fuente.
- **Exportar PDF de una conversacion con turnos de rechazo**: permitido; el PDF refleja cada rechazo tal cual, sin fuentes fabricadas (ver US6 escenario 2).
- **Intentar exportar una consulta stateless**: no es exportable, porque el sistema no guardo nada. Error claro indicando que exportar requiere una sesion (FR-224).
- **Reinicio del servicio con sesiones activas**: todas las sesiones se pierden (historial solo en memoria, FR-214). El siguiente turno con un `session_id` previo se trata como sesion expirada y se responde stateless (FR-214a); un intento de exportacion devuelve "conversacion no disponible" (FR-224a).
- **Primer turno de una sesion recien creada**: no hay historial; se comporta como stateless pero registra el turno.
- **Dos consultas concurrentes con el mismo `session_id`**: ambas se responden; el historial resultante conserva ambos turnos sin corromperse.
- **Sesion sin actividad que vence mientras no hay trafico**: la sesion se considera expirada por TTL aunque nadie la consulte; su historial deja de estar disponible.
- **Reporte PDF de una corrida de indexacion con cero documentos indexados**: el PDF se genera e informa explicitamente el resultado vacio, en lugar de fallar.
- **Conversacion larga o con muchas fuentes al exportar**: el PDF pagina el contenido; no se truncan turnos ni listas de fuentes citadas. El PDF exporta TODOS los turnos de la sesion, no solo los que entran en el limite de contexto de FR-208 (el limite acota lo que se envia al pipeline, no lo que se registra ni lo que se exporta).
- **Consulta con `session_id` mientras el indice no esta listo**: se aplica el error de indice no disponible de la Fase 1; el turno no se registra como respuesta valida.

## Requirements *(mandatory)*

### Functional Requirements

#### Conversacion multi-turno

- **FR-201**: System MUST accept an optional `session_id` on every user query. A query WITHOUT `session_id` MUST behave exactly as in Fase 1: no history is read, no history is written.
- **FR-202**: System MUST allow a user to explicitly start a conversation session and MUST return a unique session identifier.
- **FR-203**: System MUST allow a user to explicitly delete a session, discarding its history immediately.
- **FR-204**: System MUST expire sessions after a configurable TTL (Time To Live), measured from the last activity in the session. Default: 30 minutes.
- **FR-205**: System MUST reject a malformed or unknown `session_id` with a clear validation error, and MUST NOT create the session implicitly.
- **FR-206**: When a session has expired, System MUST answer the incoming query as stateless and MUST inform the user that the session expired, instead of failing the query.
- **FR-207**: System MUST record each turn of a session as the pair (user question, assistant answer).
- **FR-208**: System MUST enforce a configurable limit on how much history is included as context in each query. Default: the 5 most recent turns. When the limit is exceeded, only the most recent turns within the limit MUST be included; older turns MUST be dropped from the context without raising an error.
- **FR-209**: System MUST use conversation history ONLY to reformulate the incoming question into a self-contained query before retrieval (e.g. "y como es el tramite?" -> "como es el tramite de equivalencias?"). The history text MUST NOT be included in the generation prompt. The generator MUST see only the reformulated question and the corpus fragments retrieved for it. [Decidido 2026-07-12]
- **FR-209a**: Because the generator never receives the history (FR-209), the guarantee that history cannot become a knowledge source is STRUCTURAL, not prompt-dependent. Any design that passes raw history to the generator MUST be rejected in review as a constitutional violation of FR-210.
- **FR-210**: Every institutional claim in an answer MUST originate from content retrieved from the indexed corpus in that same turn. System MUST NOT present information taken from the history — including user-supplied assertions — as institutional fact.
- **FR-211**: When retrieved corpus context is insufficient, System MUST return the approved refusal text (FR-007 del spec 001) EVEN IF the conversation history appears to contain a relevant answer.
- **FR-212**: Answers within a session MUST include at least one institutional source URL under the same rules as FR-005 del spec 001. Being inside a session MUST NOT relax the citation obligation.
- **FR-213**: System MUST NOT repeat greeting or self-presentation text in turns after the first turn of a session.
- **FR-214**: Conversation history MUST be held in process memory only. It MUST NOT be written to disk or to any external service. A service restart MUST discard all active sessions and their history. [Decidido 2026-07-12]
- **FR-214a**: After a restart, a query carrying a `session_id` from before the restart MUST be treated as an expired/unknown session and handled per FR-206 (answered as stateless, informing the user), never as a failure.
- **FR-215**: TTL, history turn limit, and session storage parameters MUST be centrally configurable, not hardcoded.

#### Reportes PDF

- **FR-216**: System MUST allow an administrator to export the current index status as a PDF containing document count, last successful update date, covered areas, and recent failures.
- **FR-217**: System MUST allow an administrator to export the summary of an indexing run as a PDF containing update mode, timings, indexed and failed document counts, and failed-source details.
- **FR-218**: System MUST allow an administrator to export the configured sources as a PDF listing URL, area, regional/department, source type, and active status for each source.
- **FR-219**: System MUST allow a user to export a CONVERSATION as a PDF, identified by its `session_id`. The PDF MUST contain every turn of the session in order, each with the user question, the assistant answer, and the cited source URLs with page titles when available. [Decidido 2026-07-12]
- **FR-219a**: The conversation PDF MUST be built exclusively from the history the system itself recorded (FR-207). System MUST NOT accept answer content supplied by the client for inclusion in a PDF, so an exported PDF always reflects what the assistant actually answered.
- **FR-220**: When a conversation contains turns that were insufficient-context refusals, the PDF MUST include those turns and state the refusal explicitly, with no fabricated sources or content.
- **FR-221**: Every generated PDF MUST include its generation date and an identification of the issuing system.
- **FR-222**: System MUST generate all PDFs locally, without calling any external service.
- **FR-223**: System MUST return a clear error, rather than an empty or partial PDF, when the requested report subject does not exist.
- **FR-224**: Conversation PDF export REQUIRES an active session. Because a stateless query (no `session_id`) leaves no server-side record (FR-201), its answer is NOT exportable. System MUST return a clear error explaining that exporting requires a session, rather than producing an empty PDF. Users who want an exportable record MUST start a session first.
- **FR-224a**: Exporting a session whose TTL has expired, was explicitly deleted, or was lost to a restart MUST return a clear "conversation no longer available" error, never a partial or empty PDF.
- **FR-225**: Administrator-only PDF exports (FR-216, FR-217, FR-218) MUST be protected under the same operational access policy as other administrator actions (FR-026 del spec 001).

#### Trazabilidad

- **FR-226**: Each implemented component of this feature MUST trace to a user story, functional requirement, or documented decision in this specification.

### Non-Functional Requirements

- **NFR-201**: A query WITH conversation history MUST return a response or controlled error within 7 seconds for at least 95% of normal queries when local services and the index are ready. This extends the 5-second budget of SC-004 del spec 001 by at most 2 seconds; the history MUST NOT be the cause of a larger regression.
- **NFR-202**: A query WITHOUT `session_id` MUST NOT show measurable latency regression versus Fase 1, since it does not read or write history.
- **NFR-203**: A conversation PDF MUST NOT exceed 5 MB, and MUST be produced within 10 seconds under normal local conditions, for a conversation of up to 50 turns.
- **NFR-204**: An administrative report PDF MUST NOT exceed 10 MB, and MUST be produced within 15 seconds under normal local conditions.
- **NFR-205**: Session storage MUST support at least 100 concurrent active sessions in normal local conditions without degrading query experience.
- **NFR-206**: Expired session history MUST become unavailable for retrieval once the TTL has elapsed, whether or not anyone queries the session, and MUST be released from memory so that abandoned sessions do not accumulate.

### Institutional Source Requirements

Sin cambios respecto de la Fase 1. La incorporacion de historial NO altera los
tipos de fuente, las areas institucionales, la metadata requerida ni el
comportamiento de contexto insuficiente definidos en el spec 001. Este feature
NO agrega fuentes de conocimiento: agrega contexto conversacional y una capa de
exportacion.

**Insufficient Context Behavior**: sin cambios. System MUST say "No tengo
informacion suficiente sobre este tema en las fuentes institucionales
disponibles." cuando el contexto recuperado del corpus no alcanza, con o sin
sesion activa.

### Key Entities *(include if feature involves data)*

- **Conversation Session**: Una conversacion efimera identificada por `session_id`, con fecha de creacion, fecha de ultima actividad, TTL aplicable y estado (activa / expirada / borrada).
- **Conversation Turn**: Un par (pregunta del usuario, respuesta del asistente) dentro de una sesion, con orden y marca temporal. Es contexto conversacional, no conocimiento.
- **Report Request**: Un pedido de exportacion, con tipo de reporte (estado del indice, corrida de indexacion, fuentes configuradas, conversacion), sujeto referenciado y fecha de generacion.
- **Generated Report**: El documento PDF producido, con su contenido, fecha de generacion e identificacion del sistema emisor.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-201**: En pruebas de aceptacion, al menos 90% de las consultas de seguimiento que referencian un turno anterior (ej: "y como es el tramite?") se responden sobre el tema correcto sin que el usuario deba repetir el tema.
- **SC-202**: 100% de las respuestas dentro de una sesion que se fundan en contenido recuperado incluyen al menos una URL de fuente institucional, igual que en la Fase 1.
- **SC-203**: 100% de las consultas cuyo respaldo en el corpus es insuficiente devuelven el texto de rechazo aprobado, incluso cuando el historial contiene informacion aparentemente relevante. Cero casos de informacion del historial presentada como institucional.
- **SC-204**: 100% de las consultas sin `session_id` producen el mismo comportamiento observable que en la Fase 1 (retrocompatibilidad verificada por regresion).
- **SC-205**: 95% de las consultas con historial devuelven respuesta o error controlado en menos de 7 segundos en condiciones locales normales.
- **SC-206**: 100% de las sesiones vencidas por TTL dejan de exponer su historial en pruebas de aceptacion.
- **SC-207**: Los cuatro tipos de PDF (estado del indice, corrida de indexacion, fuentes configuradas, conversacion) se generan correctamente y abren sin errores en un lector de PDF estandar.
- **SC-208**: 100% de los PDF se generan sin trafico saliente hacia servicios externos, verificado durante pruebas de aceptacion.
- **SC-209**: 100% de los turnos de rechazo exportados indican el rechazo explicitamente y no contienen ninguna fuente citada.
- **SC-211**: 100% del contenido de los PDF de conversacion coincide con el historial registrado por el sistema; cero casos en que contenido enviado por el cliente termine impreso en un PDF.
- **SC-212**: En pruebas de regresion, el generador de respuestas nunca recibe texto del historial: el 100% de los prompts de generacion contienen unicamente la consulta reformulada y fragmentos del corpus (verificacion estructural de FR-209a).
- **SC-210**: En una misma sesion, el saludo/presentacion aparece a lo sumo una vez en el 100% de las conversaciones de prueba.

## Assumptions

- **TTL por defecto**: 30 minutos desde la ultima actividad. Valor configurable; se eligio como default razonable para una consulta institucional puntual. La constitucion v1.1.0 exige que sea configurable, no fija el numero.
- **Limite de historial por defecto**: los 5 turnos mas recientes. Se eligio turnos (y no tokens) como unidad por ser mas simple de razonar y testear; un limite por tokens puede especificarse mas adelante si el limite por turnos resulta insuficiente.
- **Sesiones anonimas**: como no hay login (fuera de alcance, igual que en Fase 1), una sesion no se asocia a una identidad de usuario. Quien posee el `session_id` accede al historial de esa sesion. Esto es aceptable porque el despliegue es local y las consultas no son sensibles.
- **Acceso administrativo**: los reportes PDF de administrador se protegen bajo la misma politica operativa de la Fase 1 (FR-026 del spec 001): entorno controlado u operacion manual, no autenticacion de usuarios.
- **Interfaz**: el feature se expone por la misma interfaz programatica de la Fase 1. La interfaz grafica web sigue fuera de alcance.
- **Idioma de los PDF**: espanol argentino, coherente con las respuestas del asistente.
- **Reformulacion como unico uso del historial** [Decidido 2026-07-12]: el historial se usa exclusivamente para reescribir la consulta de seguimiento en una consulta autonoma antes de buscar en el corpus. El texto del historial nunca llega al generador. Esto hace que la garantia "el historial no es fuente de conocimiento" sea estructural y no dependiente del prompt (FR-209, FR-209a). Costo aceptado: las respuestas pueden sonar algo menos conversacionales que si el modelo viera los turnos previos.
- **Historial solo en memoria** [Decidido 2026-07-12]: un reinicio del servicio descarta todas las sesiones. Se acepta porque las sesiones son efimeras por diseno (TTL 30 min) y evita introducir una capa de persistencia y un job de limpieza. Consecuencia asumida: una conversacion no exportada antes de un reinicio se pierde.
- **Exportacion ligada a la sesion** [Decidido 2026-07-12]: se exporta la conversacion completa por `session_id`, siempre desde el historial que el sistema registro. Esto garantiza que el PDF sea fiel a lo que el asistente realmente respondio, y descarta que un cliente pueda imprimir contenido alterado como si fuera institucional. Consecuencia asumida: las consultas stateless no son exportables (FR-224); para obtener un PDF hay que abrir una sesion.

## Dependencies

- Depende del pipeline de consulta de la Fase 1 (`001-institutional-assistant`), que debe estar operativo.
- Depende de la enmienda constitucional v1.1.0, que habilita historial OPT-IN y generacion local de PDF.
- Los reportes administrativos consumen datos ya producidos por la Fase 1: estado del indice (FR-018 del spec 001), corridas de indexacion (FR-017 del spec 001) y fuentes configuradas (FR-011 del spec 001). Este feature NO redefine esos datos.

## Out of Scope

- Login o autenticacion de usuarios finales (sigue fuera de alcance, igual que en Fase 1).
- Sincronizacion de sesiones entre dispositivos.
- Interfaz grafica web.
- Analytics, metricas o mineria sobre el historial de conversaciones.
- Envio de PDF por email o cualquier otro canal de distribucion.
- Ingesta de PDF como fuente de conocimiento. Este feature GENERA PDF; no los indexa. (No confundir con la exclusion de la Fase 1 sobre ingesta de PDF, que sigue vigente.)
- Titulos, resumenes o nombres automaticos de conversaciones.
- Exportacion de una respuesta aislada fuera de una sesion: las consultas stateless no son exportables (FR-224).
- Persistencia del historial en disco o supervivencia a reinicios del servicio (FR-214).
- Inclusion del historial en el prompt de generacion (FR-209a lo prohibe explicitamente).
- Formatos de exportacion distintos de PDF.
- Servicios externos de pago para cualquier funcion de este feature.
