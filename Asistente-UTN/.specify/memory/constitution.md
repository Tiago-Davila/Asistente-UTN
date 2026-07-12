<!--
Sync Impact Report
Version change: 1.0.1 -> 1.1.0 (MINOR: se relaja una restriccion y se agrega una regla sustantiva)
Modified principles: ninguno. Los Principios I-X permanecen intactos.
Modified sections:
- Restricciones de Arquitectura -> la regla "El pipeline RAG MUST ser stateless" pasa a
  "Estado conversacional OPT-IN por sesion": habilita historial efimero con TTL configurable,
  sin session_id sigue siendo stateless, y el historial NUNCA es fuente de conocimiento.
Added sections:
- Restricciones de Arquitectura -> nueva regla "Generacion de PDF" (local, open source, capa separada).
Removed sections: none
Templates requiring updates:
- .specify/templates/plan-template.md - ACTUALIZADO: la linea Constraints ya no afirma "stateless RAG queries"
- .specify/templates/spec-template.md - sin cambios necesarios (no referencia la regla de estado)
- .specify/templates/tasks-template.md - sin cambios necesarios (no referencia la regla de estado)
- specs/001-institutional-assistant/plan.md - sin cambios necesarios: describe la Fase 1, que
  efectivamente es stateless; la Fase 2 debera declarar su propio Constitution Check
Follow-up TODOs:
- La Fase 2 MUST definir en spec.md el TTL por defecto de sesion y el limite de turnos de historial.
- El Principio III enumera las capas vigentes (scraper/processor/vectorstore/rag/api) y no contempla
  aun las capas de sesion ni de PDF. No hay contradiccion directa (el principio exige separacion, no
  prohibe capas nuevas), pero si la Fase 2 introduce esas capas, considerar una enmienda MINOR que
  extienda la tabla del Principio III.
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

El alcance del corpus vigente MUST definirse en la especificacion. La capacidad
multi-regional descrita aqui es un requisito de disenio (el sistema no debe
degradarse al crecer), no una obligacion de indexar todas las regionales en la
version actual. La version actual indexa unicamente UTN-FRBA, Ingenieria en
Sistemas de Informacion, segun `spec.md`.

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

### Estado conversacional OPT-IN por sesion

El pipeline RAG MUST ser stateless por defecto. El historial de conversacion es
una capacidad OPT-IN que MUST activarse explicitamente por sesion y MUST
respetar estos limites:

- Una consulta sin `session_id` MUST tratarse como stateless, exactamente igual
  que en la Fase 1. La retrocompatibilidad es total: ningun cliente existente
  cambia de comportamiento.
- Cada sesion de conversacion MUST ser efimera y MUST tener un TTL configurable
  centralmente. Vencido el TTL, el historial MUST descartarse.
- El historial MUST usarse unicamente como contexto conversacional (por ejemplo,
  para resolver referencias anaforicas o consultas de seguimiento) y MUST NOT
  usarse jamas como fuente de conocimiento. Las respuestas MUST seguir fundadas
  exclusivamente en el corpus indexado, conforme al Principio IX: si el contexto
  recuperado del corpus es insuficiente, el sistema MUST responder "no tengo
  informacion sobre eso" aunque el historial contenga informacion aparentemente
  relevante.
- La persistencia del historial MUST ser local y MUST NOT depender de servicios
  externos de pago, en coherencia con el Stack Tecnologico No Negociable.

Fuera del historial de sesion, la persistencia se limita al corpus indexado,
metadata, base vectorial y configuracion operativa aprobada por la
especificacion.

### Generacion de PDF

Los reportes y exportaciones en PDF MUST generarse localmente con librerias
Python open source y MUST NOT depender de servicios externos de generacion o
renderizado.

La generacion de PDF MUST vivir en una capa de responsabilidad separada. Los
endpoints FastAPI y el pipeline RAG MUST NOT construir documentos PDF
directamente: MUST delegar en esa capa, coherente con los Principios II y III.

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

**Version**: 1.1.0 | **Ratified**: 2026-06-30 | **Last Amended**: 2026-07-12