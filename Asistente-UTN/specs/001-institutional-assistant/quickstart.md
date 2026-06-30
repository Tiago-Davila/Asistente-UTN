# Quickstart Validation Guide: Institutional Assistant

**Feature**: [spec.md](./spec.md)  
**Date**: 2026-06-30

This guide describes how the implemented feature should be validated after
`tasks.md` exists and implementation has been completed. It is not an
implementation script and does not create application code.

## Prerequisites

- Local Docker Compose environment available.
- Ollama service available locally with the configured LLM model.
- ChromaDB local persistence available.
- Embedding model `paraphrase-multilingual-mpnet-base-v2` available to the
  processor.
- Source configuration includes at least one public UTN HTML source for
  `ACADEMICA`.
- The implementation follows [contracts/openapi.yaml](./contracts/openapi.yaml)
  and [data-model.md](./data-model.md).

## Validation Scenario 1: Health and Empty Index

Goal: prove that the system reports dependency and index readiness clearly.

Steps after implementation:

1. Start the local services.
2. Request `GET /health`.
3. Request `GET /index/status`.
4. Submit a valid query before the index is ready.

Expected outcomes:

- Health reports local dependency state for ChromaDB and Ollama.
- Index status reports `ready: false` or zero counts when empty.
- Query returns a controlled not-ready or empty-index error, not an unsupported
  answer.

## Validation Scenario 2: Full Source Update

Goal: prove that configured public UTN sources can be processed without code
changes.

Steps after implementation:

1. Ensure source configuration contains rectorado or regional HTML sources.
2. Trigger a full rebuild through the administrative operation.
3. Review the update run summary.
4. Request `GET /index/status`.

Expected outcomes:

- The update run reports documents/fragments indexed and failures.
- Failed individual URLs are recorded without stopping the entire run.
- A completed run promotes a usable index.
- Status shows document count, fragment count, last successful update, covered
  areas, and regional coverage when configured.

## Validation Scenario 3: Successful Query With Citation

Goal: prove that a user can ask an institutional question and see a cited
answer.

Steps after implementation:

1. Use an indexed source containing academic calendar or inscription content.
2. Submit `POST /query` with a Spanish question such as
   "Cuando son las fechas de inscripcion?"
3. Review the answer and sources.

Expected outcomes:

- The answer is in Argentinian Spanish.
- `context_sufficient` is true.
- At least one source URL is present.
- Page title is included when available.
- The cited source corresponds to retrieved context.
- Normal query completion meets the 5-second user-facing target.

## Validation Scenario 4: Insufficient Context Refusal

Goal: prove that the assistant refuses unsupported answers.

Steps after implementation:

1. Submit a query outside the configured UTN corpus.
2. Review the answer and context flag.

Expected outcomes:

- `context_sufficient` is false.
- The answer is exactly:
  "No tengo informacion suficiente sobre este tema en las fuentes
  institucionales disponibles."
- No unsupported institutional claim is generated.

## Validation Scenario 5: Area Filtering

Goal: prove that optional area filtering affects retrieval scope.

Steps after implementation:

1. Ensure at least two institutional areas have indexed content.
2. Submit a query without an area filter.
3. Submit the same query with `area: ACADEMICA`.
4. Submit a query for an area with insufficient content.

Expected outcomes:

- No-filter query searches the whole usable index.
- Filtered query returns only sources from the selected area.
- Insufficient area-specific content returns the approved refusal message.

## Validation Scenario 6: Failed Update Preservation

Goal: prove that a failed update does not replace the previous usable index.

Steps after implementation:

1. Build a valid index.
2. Submit a query and record that it answers from the current index.
3. Trigger an update with one or more intentionally failing sources.
4. Submit the same query while or after the failed update.

Expected outcomes:

- The failed run is recorded as failed.
- The previous usable index remains active.
- Queries continue to use the previous index until a successful update is
  promoted.

## Validation Scenario 7: Input and Dependency Errors

Goal: prove that invalid inputs and unavailable local services produce clear
errors.

Steps after implementation:

1. Submit an empty question.
2. Submit a question over the configured maximum length.
3. Simulate local generation dependency unavailable.
4. Simulate index unavailable or not ready.

Expected outcomes:

- Invalid questions return structured validation errors.
- The response generator unavailable case returns a clear controlled error.
- Index unavailable/not-ready cases return clear structured errors.
- No internal stack traces or implementation details are exposed to users.

## Planning Notes

- The first implementation task list must include unit tests for chunk overlap,
  relevance-threshold refusal, citation integrity, semantic result ordering,
  scraper error handling, empty-page handling, and prompt context inclusion.
- The implementation phase must not add frontend work unless the spec is amended
  first.
- Acceptance data for representative institutional FAQ questions should be
  curated before final validation.
