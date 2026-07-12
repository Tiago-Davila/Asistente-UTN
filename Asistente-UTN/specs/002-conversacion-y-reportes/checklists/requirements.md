# Specification Quality Checklist: Conversacion Multi-Turno y Reportes PDF

**Purpose**: Validate specification completeness and quality before proceeding to planning
**Created**: 2026-07-12
**Feature**: [spec.md](../spec.md)

## Content Quality

- [x] No implementation details (languages, frameworks, APIs)
- [x] Focused on user value and business needs
- [x] Written for non-technical stakeholders
- [x] All mandatory sections completed

## Requirement Completeness

- [x] No [NEEDS CLARIFICATION] markers remain
- [x] Requirements are testable and unambiguous
- [x] Success criteria are measurable
- [x] Success criteria are technology-agnostic (no implementation details)
- [x] All acceptance scenarios are defined
- [x] Edge cases are identified
- [x] Scope is clearly bounded
- [x] Dependencies and assumptions identified

## Feature Readiness

- [x] All functional requirements have clear acceptance criteria
- [x] User scenarios cover primary flows
- [x] Feature meets measurable outcomes defined in Success Criteria
- [x] No implementation details leak into specification

## Constitution Alignment (v1.1.0)

- [x] Historial es OPT-IN por sesion; sin `session_id` el comportamiento es stateless (FR-201)
- [x] Sesiones efimeras con TTL configurable (FR-204)
- [x] Historial NUNCA es fuente de conocimiento; respuestas fundadas solo en el corpus (FR-209, FR-210, FR-211)
- [x] Persistencia de historial local, sin servicios externos de pago (FR-214)
- [x] PDF generado localmente con librerias open source, sin servicios externos (FR-222)
- [x] Generacion de PDF como capa separada (no vive en endpoints ni en el pipeline RAG) — a verificar en `/speckit-plan`
- [x] Principio IX intacto: obligacion de citar fuente no se relaja dentro de una sesion (FR-212)

## Notes

Validacion completa: todos los items pasan. Spec lista para `/speckit-plan`.

### Decisiones tomadas 2026-07-12 (resolvieron los 3 [NEEDS CLARIFICATION])

1. **FR-214 — durabilidad del historial**: solo en memoria. Un reinicio descarta las
   sesiones activas. Sin persistencia en disco, sin job de limpieza por archivo.
2. **FR-209 / FR-209a — uso del historial**: solo para reformular la consulta antes de
   recuperar. El texto del historial NUNCA llega al generador. La garantia de que el
   historial no es fuente de conocimiento queda ESTRUCTURAL, no dependiente del prompt.
3. **FR-219 / FR-224 — exportacion PDF**: se exporta la CONVERSACION completa por
   `session_id`, construida solo desde el historial registrado por el sistema.
   Consecuencia de alcance: las consultas stateless NO son exportables.

### Clarificaciones 2026-07-12 (sesion `/speckit-clarify`, 5 preguntas)

4. **FR-208a — tope de turnos por sesion**: default 50, configurable. Al alcanzarlo la sesion
   rechaza turnos nuevos; NO descarta los viejos. Acota memoria y mantiene el PDF completo.
5. **FR-207 / FR-207a — que se registra**: los turnos completados SI, incluidos los rechazos por
   contexto insuficiente (son respuestas legitimas). Los errores de infraestructura NO: no consumen
   cupo, no salen en el PDF, no alimentan la reformulacion. Resolvio una contradiccion interna.
6. **FR-209b / FR-209c — reformulacion**: no corre en el primer turno. Si falla, degrada a stateless
   con la pregunta original e informa; nunca falla la consulta ni inventa respuesta.
7. **SC-201 — medicion**: conjunto fijo de 20 pares, verificacion automatizada por coincidencia de
   fuentes citadas, umbral 18/20. El conjunto se define en `/speckit-plan`.
8. **FR-205a — concurrencia**: un turno a la vez por sesion; consulta concurrente sobre la misma
   sesion se rechaza con "sesion ocupada". Sesiones distintas siguen en paralelo.

### Consecuencias de alcance que el plan debe respetar

- Exportar requiere sesion. No existe exportacion de respuesta aislada.
- Una conversacion no exportada antes de un reinicio se pierde (aceptado).
- Cualquier diseno que pase historial crudo al generador es violacion constitucional (FR-209a).
- El limite de historial (FR-208, default 5 turnos) acota lo que se ENVIA al pipeline. El tope de
  sesion (FR-208a, default 50 turnos) acota lo que se GUARDA. Son dos limites distintos; el PDF
  incluye todos los turnos guardados de la sesion.
- El conjunto de evaluacion de 20 pares para SC-201 debe definirse durante `/speckit-plan`.
- El TTL por defecto (30 min) y el limite de historial (5 turnos) quedaron definidos como
  valores por defecto configurables, cumpliendo el follow-up TODO de la constitucion v1.1.0.
