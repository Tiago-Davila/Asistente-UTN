# Acceptance FAQ Dataset — UTN Institutional Assistant

**Purpose**: Representative institutional FAQ questions for SC-001 acceptance testing.  
**SC-001**: At least 90% of representative institutional FAQ questions with available
source content must receive a relevant answer with a cited source during acceptance testing.

**Traceability**: T103, SC-001, quickstart.md Scenario 3.

---

## How to Use

Each question below should be submitted to `POST /query` against a fully
indexed corpus.  For each question, record:

- `answer`: the text returned (or refusal text).
- `context_sufficient`: `true` / `false`.
- `sources`: list of cited URLs.
- `pass`: `true` if `context_sufficient=true` and at least one source URL is present;
  `false` if the refusal text was returned.

A result is acceptable (pass) if:
1. `context_sufficient` is `true` **and** at least one source URL is included, **or**
2. `context_sufficient` is `false` **and** the exact approved refusal text is returned
   (the source simply isn't in the indexed corpus — the system is correct to refuse).

SC-001 passes when ≥ 90% of questions with known indexed content return a pass result.

---

## Category: Inscripciones y Cursada (ACADEMICA)

| # | Question | Expected area | Notes |
|---|----------|---------------|-------|
| Q001 | ¿Cuándo son las fechas de inscripción al primer cuatrimestre? | ACADEMICA | Core FAQ |
| Q002 | ¿Cómo me inscribo a través de SIU Guaraní? | ACADEMICA | SIU Guaraní vocabulary |
| Q003 | ¿Cuáles son los requisitos para inscribirse a una materia? | ACADEMICA | Correlativas |
| Q004 | ¿Dónde consulto el calendario académico? | ACADEMICA | Calendar |
| Q005 | ¿Cuándo son las mesas de examen del turno diciembre? | ACADEMICA | Exam session |
| Q006 | ¿Cómo me anoto a una mesa de examen? | ACADEMICA | Exam registration |
| Q007 | ¿Cuál es la carga horaria mínima para mantener la regularidad? | ACADEMICA | Regularidad |
| Q008 | ¿Cuándo comienza el segundo cuatrimestre? | ACADEMICA | Calendar |

## Category: Trámites Administrativos (ADMINISTRATIVA)

| # | Question | Expected area | Notes |
|---|----------|---------------|-------|
| Q009 | ¿Cómo solicito un certificado de alumno regular? | ADMINISTRATIVA | Certificate |
| Q010 | ¿Dónde tramito el equivalente de materias aprobadas? | ADMINISTRATIVA | Equivalencias |
| Q011 | ¿Cuál es el horario de atención de la secretaría? | ADMINISTRATIVA | Opening hours |
| Q012 | ¿Cómo solicito la baja temporal de la carrera? | ADMINISTRATIVA | Leave |
| Q013 | ¿Qué necesito para tramitar el título? | ADMINISTRATIVA | Graduation |
| Q014 | ¿Dónde presento la documentación para el ingreso? | ADMINISTRATIVA | Admission |

## Category: Bienestar Estudiantil (BIENESTAR)

| # | Question | Expected area | Notes |
|---|----------|---------------|-------|
| Q015 | ¿La UTN tiene comedor universitario? | BIENESTAR | Dining |
| Q016 | ¿Existen becas para alumnos de bajos recursos? | BIENESTAR | Scholarships |
| Q017 | ¿Cómo accedo al servicio médico de la facultad? | BIENESTAR | Health |
| Q018 | ¿Hay guarderías o servicios para alumnos con hijos? | BIENESTAR | Childcare |
| Q019 | ¿Qué actividades deportivas ofrece la facultad? | BIENESTAR | Sports |

## Category: Extensión y Vinculación (EXTENSION)

| # | Question | Expected area | Notes |
|---|----------|---------------|-------|
| Q020 | ¿Qué cursos de extensión ofrece la UTN? | EXTENSION | Courses |
| Q021 | ¿Cómo me inscribo a un curso de posgrado? | EXTENSION | Postgrad |
| Q022 | ¿La UTN ofrece pasantías laborales? | EXTENSION | Internships |
| Q023 | ¿Cómo puedo participar en proyectos de investigación? | EXTENSION | Research |

## Category: Vocabulario Universitario Argentino (Cross-area)

| # | Question | Expected area | Notes |
|---|----------|---------------|-------|
| Q024 | ¿Qué es la cursada y cómo se diferencia del examen final? | ACADEMICA | AR vocabulary |
| Q025 | ¿Qué significa "libre" en la UTN? | ACADEMICA | AR vocabulary: condición libre |
| Q026 | ¿Cómo funciona el sistema de créditos o unidades? | ACADEMICA | Credits |
| Q027 | ¿Qué es el decanato y para qué sirve? | ADMINISTRATIVA | AR institutional term |

## Category: Fuera del Corpus (Expected Refusal)

These questions are outside the expected UTN corpus and must return the refusal text.

| # | Question | Expected outcome |
|---|----------|-----------------|
| Q028 | ¿Cuál es la capital de Francia? | Refusal (out of scope) |
| Q029 | ¿Cómo se programa en Python? | Refusal (out of scope) |
| Q030 | ¿Qué películas hay en el cine esta semana? | Refusal (out of scope) |

---

## Acceptance Criteria

- **SC-001 PASS**: ≥ 90% of Q001–Q027 return `context_sufficient=true` with a cited
  source when the corpus contains the relevant content.
- **SC-003 PASS**: 100% of Q028–Q030 return the exact refusal text.
- **SC-002 PASS**: 100% of passing answers include at least one source URL.

---

## Recording Template

Copy and fill this table for each test run:

```
| # | Question | context_sufficient | sources | pass | notes |
|---|----------|--------------------|---------|------|-------|
| Q001 | ... | true/false | url | Y/N | |
```
