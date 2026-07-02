<!--
Sync Impact Report
Version change: template -> 1.0.0
Modified principles:
- Template placeholders -> I. La especificacion manda sobre la implementacion
- Template placeholders -> II. Dominio modelado con claridad conceptual
- Template placeholders -> III. Responsabilidades separadas por capas
- Template placeholders -> IV. Python sin anti-patrones institucionales
- Template placeholders -> V. Tipos y constantes para valores cerrados
- Template placeholders -> VI. Patrones de diseño solo si simplifican
- Template placeholders -> VII. Reglas de negocio testeadas
- Template placeholders -> VIII. Escalabilidad sin degradar busqueda
- Template placeholders -> IX. Respuestas claras, fundadas y honestas
- Template placeholders -> X. Fases SDD sin codigo
Added sections:
- Stack Tecnologico No Negociable
- Restricciones de Arquitectura
- Flujo de Trabajo y Control de Versiones
Removed sections:
- Placeholder SECTION_2_NAME
- Placeholder SECTION_3_NAME
Templates requiring updates:
- .specify/templates/plan-template.md - updated
- .specify/templates/spec-template.md - updated
- .specify/templates/tasks-template.md - updated
- .specify/templates/checklist-template.md - updated
- .specify/templates/commands/*.md - not present
Follow-up TODOs: none
-->
# Asistente Inteligente Institucional UTN Constitution

## Core Principles

### I. La especificacion manda sobre la implementacion
Toda funcionalidad MUST estar trazada a una historia de usuario, requisito
funcional o decision documentada en la especificacion vigente. Ningun scraper,
pipeline RAG, endpoint, job, interfaz o componente de infraestructura puede
existir sin respaldo en `spec.md`, `plan.md` o `tasks.md`. El alcance no
documentado MUST rechazarse o convertirse primero en una enmienda de
especificacion.

Rationale: el proyecto usa SDD para mantener utilidad institucional real,
evitar crecimiento accidental y preservar una arquitectura auditable.

### II. Dominio modelado con claridad conceptual
Cada modulo MUST tener una responsabilidad unica y reconocible dentro del
dominio institucional. La obtencion de contenido, la limpieza, el chunking, la
generacion de embeddings, la busqueda semantica, la generacion de respuestas y
la exposicion HTTP MUST permanecer conceptualmente separados. Los nombres de
modulos, DTOs, entidades y servicios MUST expresar conceptos del dominio UTN o
del pipeline RAG sin mezclar niveles de abstraccion.

Rationale: un modelo conceptual claro facilita mantenimiento, testing y
transferencia de conocimiento entre estudiantes, docentes y administradores.

### III. Responsabilidades separadas por capas
La arquitectura MUST respetar estas capas y responsabilidades:

| Capa | Responsabilidad |
|------|-----------------|
| `scraper/` | Obtencion y limpieza inicial de contenido desde sitios web de la UTN |
| `processor/` | Chunking, generacion de embeddings y carga en la base vectorial |
| `vectorstore/` | Abstraccion de ChromaDB para busqueda semantica y persistencia |
| `rag/` | Orquestacion del pipeline: recuperacion de contexto y generacion de respuesta |
| `api/` | Endpoints FastAPI, DTOs y validacion de entrada/salida |

Los endpoints FastAPI MUST delegar la logica de negocio a servicios de dominio
o de aplicacion. Los controladores MUST NOT ejecutar busquedas vectoriales ni
construir prompts RAG directamente.

Rationale: separar capas reduce acoplamiento y permite reemplazar piezas como
ChromaDB, Ollama o scrapers sin reescribir toda la aplicacion.

### IV. Python sin anti-patrones institucionales
El codigo Python MUST evitar anti-patrones que degraden mantenibilidad:

- La logica de negocio MUST NOT vivir dentro de endpoints FastAPI.
- Las busquedas vectoriales MUST NOT invocarse directamente desde controladores.
- URLs, nombres de modelos, umbrales, delays y parametros operativos MUST vivir
  en `config/settings.py` o en configuracion tipada equivalente.
- La limpieza de texto MUST tener una unica implementacion reutilizable.
- El codigo MUST apuntar a Python 3.11+ y usar tipos donde ayuden a validar
  contratos entre capas.

Rationale: el asistente sera usado como referencia de arquitectura RAG en
Python; por eso el codigo debe ensenar buenas practicas ademas de funcionar.

### V. Tipos y constantes para valores cerrados
Los valores cerrados MUST representarse con `Enum`, constantes tipadas o tipos
equivalentes. Esto incluye, como minimo, areas institucionales
`ACADEMICA`, `ADMINISTRATIVA` y `BIENESTAR`; tipos de fuente `WEB`, `PDF` y
`MANUAL`; y estados de indexacion. El uso de strings sueltos para estos valores
MUST rechazarse en review.

Rationale: los valores cerrados aparecen en scraping, metadata, filtrado,
indexacion y respuestas; tiparlos evita errores silenciosos.

### VI. Patrones de diseno solo si simplifican
Los patrones de diseno MAY usarse unicamente cuando reduzcan complejidad real,
mejoren testing o faciliten reemplazos futuros. Una abstraccion sobre ChromaDB,
por ejemplo, MUST justificarse si permite testear, persistir o sustituir la
base vectorial con menor costo. Los patrones que solo agregan capas sin mejorar
claridad, pruebas o evolucion MUST NOT implementarse.

Rationale: el proyecto prioriza claridad y utilidad institucional por encima de
arquitectura ornamental.

### VII. Reglas de negocio testeadas
Toda regla de negocio importante MUST tener tests. Como minimo:

- El chunking MUST probar solapamiento correcto y limites de fragmento.
- La busqueda semantica MUST probar ordenamiento por relevancia.
- El pipeline RAG MUST probar que el contexto recuperado se incluye en el prompt
  enviado al LLM.
- Los scrapers MUST probar errores HTTP, paginas vacias y manejo de contenido
  inutilizable.
- Las reglas de umbral de similitud MUST probar que el asistente responde
  "no tengo informacion sobre eso" cuando el contexto no alcanza.

Rationale: la confianza institucional depende de respuestas trazables y
comportamiento verificable, no de demos aisladas.

### VIII. Escalabilidad sin degradar busqueda
El sistema MUST poder indexar contenido de multiples regionales y departamentos
sin recorrer documentos completos en memoria para responder consultas. La
busqueda semantica MUST operar siempre sobre ChromaDB persistente u otra base
vectorial aprobada por una enmienda constitucional. Las listas en memoria MAY
usarse solo en tests unitarios, fixtures o transformaciones previas a la carga.

Rationale: el valor del asistente depende de mantener calidad y latencia de
busqueda a medida que crece el corpus institucional.

### IX. Respuestas claras, fundadas y honestas
La interfaz del asistente MUST priorizar claridad para estudiantes, docentes y
personal administrativo. Las respuestas MUST estar en lenguaje natural en
espanol argentino, indicar la fuente institucional cuando exista metadata
suficiente y abstenerse de inventar. Si el contexto recuperado es insuficiente o
la similitud semantica queda por debajo del umbral configurado, el sistema MUST
responder "no tengo informacion sobre eso" o una variante equivalente aprobada
por especificacion. El pipeline MUST NOT generar respuestas sin contexto valido.

Rationale: una respuesta honesta y con fuente es mas util institucionalmente que
una respuesta fluida pero no verificable.

### X. Fases SDD sin codigo
Durante `/speckit.specify`, `/speckit.clarify`, `/speckit.checklist` y
`/speckit.plan`, el agente MUST producir solamente artefactos Markdown y MUST
NOT escribir codigo de aplicacion, tests, configuracion ejecutable ni
infraestructura. La implementacion comienza solo cuando exista un `tasks.md`
validado.

Rationale: separar especificacion, planificacion e implementacion protege la
trazabilidad y evita decisiones tecnicas prematuras.

## Stack Tecnologico No Negociable

El proyecto MUST usar el siguiente stack salvo enmienda constitucional:

| Componente | Tecnologia |
|------------|------------|
| Lenguaje | Python 3.11+ |
| Scraping | BeautifulSoup4 + Playwright |
| Embeddings | sentence-transformers `paraphrase-multilingual-mpnet-base-v2` |
| Base vectorial | ChromaDB persistente local |
| LLM local | Ollama via API compatible OpenAI |
| API | FastAPI |
| Contenedores | Docker Compose |
| Gestion de proyecto | GitHub + SDD con Spec Kit |

El sistema MUST correr 100% local y MUST NOT depender de servicios externos de
pago como OpenAI, Pinecone u otros proveedores SaaS para funciones centrales.

## Restricciones de Arquitectura

Ollama y ChromaDB MUST correr en Docker. El scraper y el procesador MUST poder
ejecutarse tambien en contenedores. Los modelos de Ollama MUST persistir en un
volumen Docker para evitar descargas repetidas.

El scraper MUST respetar `robots.txt` y aplicar delays configurables entre
requests para no sobrecargar servidores de la UTN. Las URLs base, politicas de
delay, parametros de chunking, nombres de modelos, umbrales de similitud y
opciones de persistencia MUST configurarse centralmente.

El pipeline RAG MUST ser stateless: cada consulta es independiente y esta
version MUST NOT guardar historial de conversacion. La persistencia se limita al
corpus indexado, metadata, base vectorial y configuracion operativa aprobada por
la especificacion.

## Flujo de Trabajo y Control de Versiones

Los artefactos SDD (`constitution.md`, `spec.md`, `plan.md`, `tasks.md`) MUST
versionarse bajo `specs/` o en la ubicacion de memoria/proyecto definida por
Spec Kit. Las ramas de trabajo MUST seguir esta politica:

- `main`: produccion, protegida por ruleset.
- `develop`: integracion.
- `feature/<nombre>`: trabajo individual, con PR hacia `develop`.

Cada PR MUST demostrar trazabilidad entre tareas, requisitos y cambios de
codigo. Los reviewers MUST verificar cumplimiento constitucional, tests de
reglas de negocio, configuracion centralizada y ausencia de codigo no
especificado.

## Governance

Esta constitucion tiene prioridad sobre practicas informales, preferencias de
implementacion y documentacion secundaria. Cuando exista conflicto, la
constitucion prevalece; luego la especificacion aprobada; luego el plan; luego
las tareas.

Las enmiendas MUST realizarse mediante cambio documentado a este archivo,
incluyendo reporte de impacto sobre plantillas, especificaciones activas y
flujo de trabajo. Cada enmienda MUST actualizar la version segun SemVer:

- MAJOR: redefine o elimina principios obligatorios de forma incompatible.
- MINOR: agrega principios, secciones o reglas sustantivas.
- PATCH: aclara redaccion sin cambiar obligaciones.

Toda feature MUST pasar el Constitution Check durante planificacion y repetirlo
despues del diseno. Las violaciones MUST documentarse en `plan.md` con
justificacion y alternativa mas simple rechazada; si contradicen un MUST, la
feature no puede avanzar sin enmienda constitucional.

**Version**: 1.0.0 | **Ratified**: 2026-06-30 | **Last Amended**: 2026-06-30
