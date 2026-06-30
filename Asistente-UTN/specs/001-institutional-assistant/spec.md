# Feature Specification: Institutional Assistant

**Feature Branch**: `[001-institutional-assistant]`

**Created**: 2026-06-30

**Status**: Draft

**Input**: User description: "Desarrollar un asistente inteligente institucional para la UTN que permita responder consultas frecuentes de estudiantes, docentes y personal administrativo, centralizando informacion institucional obtenida desde sitios web oficiales de la universidad. No implementar codigo todavia."

## Clarifications

### Session 2026-06-30

- Q: Cual debe ser la politica de acceso para la version inicial? -> A: Consulta publica local; acciones administrativas protegidas por entorno/operacion manual.
- Q: Como debe definirse el umbral minimo de relevancia para permitir respuestas? -> A: Umbral global configurable con valor inicial definido durante planificacion.
- Q: Que informacion de fuente debe ver el usuario en cada respuesta? -> A: URL y titulo de pagina cuando este disponible.
- Q: Que debe significar actualizacion incremental en la version inicial? -> A: Incremental re-procesa solo fuentes seleccionadas por el administrador.
- Q: Que alcance regional debe tener una instalacion del asistente? -> A: Cada instalacion puede cubrir rectorado y regionales configuradas.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Consulta institucional general (Priority: P1)

Como estudiante de la UTN, quiero hacer una pregunta en espanol sobre tramites,
calendarios academicos, inscripciones o servicios, para recibir una respuesta
clara sin navegar por multiples paginas institucionales.

**Why this priority**: Es el flujo principal del asistente y entrega valor
directo a la comunidad universitaria.

**Independent Test**: Con un indice institucional cargado, realizar una pregunta
frecuente y verificar que la respuesta sea comprensible, este en espanol
argentino y cite al menos una fuente institucional.

**Acceptance Scenarios**:

1. **Given** que existe contenido institucional indexado sobre inscripciones, **When** un estudiante pregunta "Cuando son las fechas de inscripcion?", **Then** recibe una respuesta en lenguaje natural con informacion relevante y una fuente institucional.
2. **Given** que el asistente tiene contexto suficiente para responder, **When** el usuario envia una consulta valida, **Then** la respuesta se entrega en menos de 5 segundos en condiciones normales de disponibilidad.
3. **Given** que el usuario usa vocabulario universitario argentino, **When** pregunta por "cursada", "mesa de examen" o "SIU Guarani", **Then** el asistente interpreta la consulta dentro del contexto institucional disponible.

---

### User Story 2 - Respuesta honesta ante falta de informacion (Priority: P1)

Como usuario del asistente, quiero que el sistema me informe cuando no tiene
informacion suficiente sobre mi consulta, para no recibir respuestas inventadas
que puedan inducirme a error.

**Why this priority**: La confiabilidad institucional depende de no inventar
respuestas ni presentar informacion sin respaldo.

**Independent Test**: Realizar una consulta fuera del alcance del corpus
institucional y verificar que el asistente rechace responder sin generar
contenido no respaldado.

**Acceptance Scenarios**:

1. **Given** que ningun contenido recuperado alcanza el umbral minimo de relevancia configurado, **When** el usuario realiza una pregunta, **Then** el asistente responde "No tengo informacion suficiente sobre este tema en las fuentes institucionales disponibles."
2. **Given** que la informacion recuperada es irrelevante o insuficiente, **When** el asistente prepara la respuesta, **Then** no incluye afirmaciones que no provengan de fuentes recuperadas.

---

### User Story 3 - Indicacion de fuente institucional (Priority: P1)

Como usuario del asistente, quiero saber de donde proviene la informacion
recibida, para poder verificarla o profundizar en el sitio oficial.

**Why this priority**: La fuente permite auditoria, confianza y continuidad del
tramite fuera del asistente.

**Independent Test**: Hacer una consulta con respuesta disponible y verificar
que la respuesta incluya al menos una URL institucional y el titulo de pagina
cuando este disponible, correspondientes al contenido usado.

**Acceptance Scenarios**:

1. **Given** que la respuesta se basa en contenido institucional recuperado, **When** el asistente responde, **Then** incluye al menos una URL de origen.
2. **Given** que el titulo de pagina esta disponible en la fuente, **When** el asistente responde, **Then** muestra ese titulo junto a la URL.
3. **Given** que se muestra una fuente, **When** se compara con el contenido usado para responder, **Then** la URL corresponde a uno de los fragmentos recuperados.

---

### User Story 4 - Actualizacion del indice institucional (Priority: P1)

Como administrador del sistema, quiero ejecutar la actualizacion de fuentes e
indice institucional para rectorado y regionales configuradas, para mantener las
respuestas alineadas con los cambios de los sitios oficiales de la UTN.

**Why this priority**: Sin actualizacion controlada, el asistente pierde vigencia
y puede responder con informacion institucional desactualizada.

**Independent Test**: Ejecutar una actualizacion sobre fuentes configuradas y
verificar el resumen de documentos procesados, fallidos y estado final del
indice, sin afectar el indice anterior si la actualizacion falla.

**Acceptance Scenarios**:

1. **Given** que existen fuentes institucionales configuradas para rectorado o regionales, **When** el administrador dispara una actualizacion, **Then** el proceso obtiene contenido sin requerir cambios de codigo.
2. **Given** que la actualizacion finaliza, **When** se presenta el resultado, **Then** informa cuantos documentos fueron indexados y cuantos fallaron.
3. **Given** que una actualizacion falla a mitad del proceso, **When** usuarios realizan consultas, **Then** siguen usando el indice anterior intacto.
4. **Given** que una fuente individual devuelve error, **When** el proceso continua con otras fuentes, **Then** registra la fuente fallida sin detener toda la ejecucion.
5. **Given** que el administrador elige una actualizacion incremental, **When** selecciona un subconjunto de fuentes configuradas, **Then** solo esas fuentes se re-procesan.

---

### User Story 5 - Disponibilidad y errores claros (Priority: P1)

Como usuario del asistente, quiero recibir mensajes claros cuando el sistema no
puede responder, para saber si debo corregir mi consulta o intentarlo mas tarde.

**Why this priority**: Los errores claros evitan frustracion y reducen consultas
de soporte.

**Independent Test**: Simular pregunta invalida, indice no listo y generador de
respuestas no disponible; verificar que cada caso devuelva un mensaje claro y
accionable.

**Acceptance Scenarios**:

1. **Given** que el usuario envia una pregunta vacia, **When** el sistema valida la consulta, **Then** devuelve un error de validacion y no intenta generar una respuesta.
2. **Given** que el indice institucional no esta listo, **When** el usuario consulta, **Then** el sistema informa que el indice no esta disponible.
3. **Given** que el generador local de respuestas no esta disponible, **When** el usuario consulta, **Then** el sistema devuelve un error claro sin exponer detalles internos.

---

### User Story 6 - Filtro por area institucional (Priority: P2)

Como estudiante, docente o administrativo, quiero filtrar mi consulta por area
institucional, para obtener resultados mas precisos y relevantes a mi situacion.

**Why this priority**: Mejora precision, pero el asistente ya entrega valor con
busqueda general sobre todo el indice.

**Independent Test**: Ejecutar la misma consulta con y sin filtro de area y
verificar que el resultado filtrado use solo fuentes del area seleccionada.

**Acceptance Scenarios**:

1. **Given** que el usuario selecciona un area institucional, **When** realiza una consulta, **Then** los resultados provienen exclusivamente de contenido asociado a esa area.
2. **Given** que el usuario no selecciona area, **When** realiza una consulta, **Then** la busqueda abarca todo el indice disponible.
3. **Given** que un area no tiene contenido suficiente, **When** el usuario consulta dentro de esa area, **Then** el sistema informa que no tiene informacion suficiente en las fuentes disponibles.

---

### User Story 7 - Estado del indice institucional (Priority: P2)

Como administrador del sistema, quiero consultar el estado actual del indice,
para saber si el contenido esta actualizado y que fuentes estan cubiertas.

**Why this priority**: Permite operacion y monitoreo, aunque no es parte del
flujo principal de consulta.

**Independent Test**: Consultar el estado del indice y verificar que muestre
cantidad de documentos, fecha de ultima actualizacion, areas cubiertas y fallos
recientes sin abrir almacenamiento interno.

**Acceptance Scenarios**:

1. **Given** que existe un indice construido, **When** el administrador consulta su estado, **Then** ve cantidad de documentos, fecha de ultima actualizacion y areas cubiertas.
2. **Given** que hubo fallos en una actualizacion reciente, **When** el administrador consulta el estado, **Then** ve un resumen de fallos suficiente para diagnosticar fuentes problematicas.

### Edge Cases

- Pregunta vacia: el sistema devuelve error de validacion y no genera respuesta.
- Pregunta mayor a 2000 caracteres: el sistema la rechaza con mensaje claro.
- Pagina fuente vacia, compuesta solo por scripts o sin texto util: el contenido se descarta y se registra el caso.
- Todos los resultados recuperados son irrelevantes: el asistente informa que no tiene informacion suficiente.
- El generador local de respuestas excede el tiempo maximo esperado: el sistema devuelve error controlado.
- Una actualizacion ocurre mientras hay consultas activas: las consultas usan el indice anterior hasta que la nueva carga finalice correctamente.
- Una URL institucional devuelve error: se registra como fallida y el proceso continua con las demas fuentes.
- Falta un recurso local necesario para responder o procesar contenido: el sistema informa claramente que recurso falta.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST allow users to submit natural-language questions in Argentinian Spanish about UTN institutional procedures, calendars, regulations, inscriptions, services, and resources.
- **FR-002**: System MUST validate that each question is non-empty and does not exceed a configurable maximum length, assumed initially as 2000 characters.
- **FR-003**: System MUST retrieve relevant institutional content before generating an answer.
- **FR-004**: System MUST answer in natural Argentinian Spanish.
- **FR-005**: System MUST include at least one institutional source URL for every answer based on retrieved content and MUST include the page title when available.
- **FR-006**: System MUST refuse to answer when retrieved context is insufficient or below the configured global relevance threshold.
- **FR-007**: System MUST use the refusal text "No tengo informacion suficiente sobre este tema en las fuentes institucionales disponibles." when it cannot answer from available sources.
- **FR-008**: System MUST avoid generating claims that are not supported by retrieved institutional context.
- **FR-009**: System MUST allow users to optionally filter queries by institutional area.
- **FR-010**: System MUST search across all indexed content when the user does not provide an area filter.
- **FR-011**: System MUST allow an administrator to configure public UTN web sources without changing application code.
- **FR-012**: System MUST extract useful text from configured public UTN web pages while excluding navigation, scripts, menus, and irrelevant page elements.
- **FR-013**: System MUST associate extracted content with source URL, extraction date, source type, institutional area, and regional or department when available.
- **FR-014**: System MUST continue a source update when an individual URL fails, and MUST record the failed URL and reason.
- **FR-015**: System MUST support complete re-indexing and incremental updates where incremental means re-processing administrator-selected configured sources.
- **FR-016**: System MUST preserve the previous usable index until a new update is confirmed as successful.
- **FR-017**: System MUST report how many documents or fragments were indexed and how many failed in each update.
- **FR-018**: System MUST allow an administrator to view index status, including document count, last successful update date, covered areas, and recent failures.
- **FR-019**: System MUST allow an administrator to rebuild the index completely.
- **FR-020**: System MUST provide a programmatic query interface that accepts a question and returns the answer, source information, and clear errors when the service cannot answer.
- **FR-021**: System MUST provide clear structured errors when the response generator is unavailable, the index is empty, or the index is not ready.
- **FR-022**: System MUST keep operational values configurable, including source URLs, area definitions, relevance threshold, question length limit, source update delay, chunk sizing, and model choices.
- **FR-023**: System MUST respect public site crawling rules and avoid overloading institutional servers during source updates.
- **FR-024**: Each implemented component MUST trace to a user story, functional requirement, or documented decision in this specification.
- **FR-025**: System MUST allow local query access without end-user login in the initial version.
- **FR-026**: System MUST restrict administrator-only actions to protected operational access, such as a controlled local environment or manual operator execution, until a later authentication feature is specified.
- **FR-027**: System MUST allow each installation to cover rectorado and one or more configured regionales or departments.

### Institutional Source Requirements *(include for RAG/content features)*

- **Source Types**: WEB for the initial version.
- **Institutional Areas**: ACADEMICA, ADMINISTRATIVA, BIENESTAR, and EXTENSION are supported as configured areas for this feature.
- **Required Source Metadata**: URL, extraction date, source type, institutional area, regional or department when available, and page title when available.
- **User-Visible Source Display**: Answers show source URL and page title when available; exact quoted fragments are not required in the initial version.
- **Freshness Expectations**: Administrators can refresh sources on demand; users can see or administrators can verify the last successful update date.
- **Insufficient Context Behavior**: System MUST say "No tengo informacion suficiente sobre este tema en las fuentes institucionales disponibles." when context is not enough.
- **Relevance Threshold Policy**: A single global relevance threshold is configurable for the initial version, and its initial value is defined during planning.

### Key Entities *(include if feature involves data)*

- **Institutional Source**: A public UTN web location configured for extraction, with URL, associated area, regional or department, source type, active status, and crawling expectations.
- **Extracted Document**: Useful institutional text obtained from a source, with URL, title when available, extraction date, area, regional or department, and processing status.
- **Content Fragment**: A searchable portion of an extracted document, with source metadata, index date, relevance information when retrieved, and linkage to its original document.
- **User Query**: A question submitted by a student, docente, administrativo, or administrator-facing process, optionally including an area filter.
- **Assistant Answer**: The response shown to the user, including answer text, source references, and refusal or error state when applicable.
- **Index Update Run**: An administrator-triggered operation that records start/end time, update mode, counts of indexed and failed items, status, and failure details.
- **Index Status**: A summary of the current searchable corpus, including document count, last update, covered areas, and readiness.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: At least 90% of representative institutional FAQ questions with available source content receive a relevant answer with a cited source during acceptance testing.
- **SC-002**: 100% of answers generated from retrieved content include at least one institutional source URL and include the page title when available.
- **SC-003**: 100% of out-of-scope or insufficient-context questions return the approved refusal message instead of an unsupported answer.
- **SC-004**: Users receive a response or controlled error within 5 seconds for at least 95% of normal queries when local services and the index are ready.
- **SC-005**: Administrators can complete a source update without code changes and receive counts of indexed and failed items at the end of every run.
- **SC-006**: A failed update never replaces the last known usable index in acceptance testing.
- **SC-007**: The searchable corpus supports at least 50,000 fragments while preserving expected query experience in normal local conditions.
- **SC-008**: At least 90% of pilot users can identify the source link used for an answer without assistance.

## Assumptions

- The initial version supports public UTN HTML pages only; PDF and internal system integrations are out of scope.
- The query interface is public within the local deployment environment for the initial version; administrator actions are protected by controlled environment access or manual operator execution until a later authentication feature is specified.
- The relevance threshold is configurable with a single global default for the initial version; the initial numeric value is selected during planning and area-specific thresholds can be specified later if needed.
- Source display includes URL and page title when available; exact quoted snippets are not required in the initial version.
- Institutional area filters are optional for users and configurable by administrators.
- Incremental updates re-process only administrator-selected configured sources in the initial version; automatic change detection is out of scope unless specified later.
- Each installation may cover rectorado plus one or more configured regionales or departments; multi-regional coverage is driven by configured sources.
- Source inclusion and exclusion lists are administrator-configured, with ephemeral news and past events excluded unless explicitly included.

## Out of Scope

- User login or end-user authentication.
- Conversation history or multi-turn memory.
- Graphical web interface.
- Multi-language support.
- Direct integration with SIU Guarani or other internal systems.
- PDF generation or reporting.
- Proactive recommendations without a user query.
- PDF source ingestion in the initial version.
- Paid external services for core query, indexing, storage, or generation behavior.
- Automatic detection of modified pages for incremental updates.
