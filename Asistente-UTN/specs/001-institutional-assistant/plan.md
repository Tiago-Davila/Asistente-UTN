# Implementation Plan: Institutional Assistant

**Branch**: `[001-institutional-assistant]` | **Date**: 2026-06-30 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/001-institutional-assistant/spec.md`

**Note**: Planning artifact only. No application code, tests, executable config,
or infrastructure is implemented in this phase.

## Summary

Build the initial UTN institutional assistant as a local RAG system that answers
natural-language questions in Argentinian Spanish from configured public UTN
HTML sources. The version covers query, source citation, insufficient-context
refusal, optional area filtering, administrator-triggered indexing, index
status, and controlled error responses. Web frontend work is explicitly out of
scope for this feature even though the meta architecture may include it later.

## Technical Context

**Language/Version**: Python 3.11+

**Primary Dependencies**: FastAPI, Pydantic v2, BeautifulSoup4, httpx,
Playwright, sentence-transformers, ChromaDB, Ollama-compatible OpenAI client,
pytest, pytest-mock

**Storage**: Local persistent ChromaDB; Docker volumes for Ollama models and
ChromaDB persistence; file-based source configuration

**Testing**: pytest, pytest-mock, ChromaDB PersistentClient test fixture in a
temporary directory, HTML fixtures for scraper tests

**Target Platform**: Local Docker Compose environment

**Project Type**: Python RAG web service with scraper and processor workers;
frontend excluded from this feature

**Performance Goals**: 95% of normal queries return an answer or controlled
error within 5 seconds; index status returns in under 1 second; corpus supports
at least 50,000 fragments while preserving expected query experience

**Constraints**: 100% local runtime; no paid external core services; stateless
RAG queries; public UTN HTML only; robots.txt compliance; configured request
delays; no end-user login in initial version; administrator actions protected
by controlled local environment or manual operator execution

**Scale/Scope**: The architecture supports an installation covering rectorado
and one or more configured regionales/departments via source configuration
(FR-027). The current version, however, is configured for a single scope:
UTN-FRBA, Ingenieria en Sistemas de Informacion (FR-028); no other regional or
department sources are configured. Initial source type WEB only; areas
ACADEMICA, ADMINISTRATIVA, BIENESTAR, EXTENSION remain supported as configured
areas, with the current FRBA-Sistemas corpus using the applicable subset.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Traceability**: PASS. Planned components map to FR-001 through FR-028 and
  user stories US1-US7. Frontend from the meta context is excluded because the
  spec lists graphical web interface out of scope.
- **Layer separation**: PASS. Planned layout keeps scraper, processor,
  vectorstore, rag, api, config, and infra responsibilities separate.
- **Configuration**: PASS. Source URLs, areas, relevance threshold, top_k,
  question length, delays, model names, timeouts, and persistence paths are
  planned as centralized settings.
- **Closed values**: PASS. Institutional areas, source types, and indexing
  states are planned as Enums/constants.
- **Local-only stack**: PASS. ChromaDB and Ollama run locally; no OpenAI,
  Pinecone, or paid SaaS dependency is part of the core behavior.
- **Business-rule tests**: PASS. Tasks must include tests for chunk overlap,
  semantic relevance ordering, prompt context inclusion, scraper failures and
  empty pages, index preservation, citation integrity, and threshold refusal.
- **Search scalability**: PASS. Runtime semantic search uses ChromaDB with
  metadata filtering; no full-document in-memory scans for query serving. The
  single-scope FRBA restriction (FR-028) does not narrow this guarantee: it is
  a configured corpus boundary, not an architectural one. Principle VIII 1.0.1
  separates the multi-regional design capacity (still required) from the
  currently indexed scope, so FR-028 and FR-027 do not conflict.
- **Answer integrity**: PASS. Responses use Argentinian Spanish, cite URL and
  title when available, and refuse insufficient context with the approved
  text. If retrieved context exceeds the relevance threshold but no retrieved
  fragment carries a source URL, the system returns the insufficient-context
  refusal instead of an uncited answer (FR-005, revised 2026-07-10).
- **SDD phase discipline**: PASS. This phase creates Markdown/YAML design
  artifacts only; implementation waits for validated `tasks.md`.

## Project Structure

### Documentation (this feature)

```text
specs/001-institutional-assistant/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── openapi.yaml
└── checklists/
    ├── requirements.md
    └── rag-requirements.md
```

### Source Code (target project layout)

```text
utn-assistant/
├── api/             # FastAPI endpoints, DTOs, dependency wiring, error mapping
├── config/          # typed settings and source configuration loading
├── infra/           # Docker Compose and local service configuration
├── processor/       # text cleaning, chunking, embeddings, index loading
├── rag/             # domain rules and application services for answering
├── scraper/         # robots-aware UTN HTML extraction
├── vectorstore/     # ChromaDB repository abstraction
└── tests/           # unit, integration, contract, fixtures
```

**Structure Decision**: Use the constitution-defined backend/RAG layers. Do not
create `frontend/` for this feature because `spec.md` excludes graphical web UI
from the initial version.

## Phase 0: Research Summary

Detailed decisions are recorded in [research.md](./research.md).

- Use one ChromaDB collection with metadata filters instead of one collection
  per area.
- Use configurable chunk size and overlap with initial defaults documented in
  research.
- Use a configurable global relevance threshold with initial planning value
  `0.65`.
- Limit retrieval to configurable `top_k`, default 5 and maximum 10.
- Use static scraping with httpx and BeautifulSoup first; use Playwright only
  for configured JS-dependent sources.
- Preserve the previous usable index with a staging/swap update strategy.
- Keep administrator actions protected by local operational controls in this
  feature; full auth is out of scope.

## Phase 1: Design Summary

Detailed design artifacts:

- [data-model.md](./data-model.md): domain entities, fields, validation rules,
  relationships, and state transitions.
- [contracts/openapi.yaml](./contracts/openapi.yaml): REST API contract for
  query, index status, rebuild, delete, and health.
- [quickstart.md](./quickstart.md): validation guide for local end-to-end
  scenarios once implementation tasks exist.

## Post-Design Constitution Check

- **Traceability**: PASS. Data model entities and API contract map to FRs and
  US1-US7, including FR-027/FR-028: `regional`/`covered_regionales` fields
  remain part of the data model and contract (architecture capacity), while
  the currently configured sources are FRBA-Sistemas only (current scope). No
  frontend contract is generated.
- **Layer separation**: PASS. Contracts expose API surface only; data model
  keeps domain concepts independent from infrastructure details.
- **Configuration**: PASS. Research and data model identify configuration-owned
  values.
- **Closed values**: PASS. Enums are documented for area, source type, and
  indexing status.
- **Local-only stack**: PASS. Contracts do not introduce external paid services.
- **Business-rule tests**: PASS. Quickstart and future tasks must validate
  refusal, citation, update preservation, scraper failures, and status.
- **Search scalability**: PASS. Research chooses ChromaDB metadata filtering
  and top_k limits. The FRBA-only current scope (FR-028) is a source
  configuration choice, not a schema or architecture restriction; regional
  metadata fields stay generic per Principle VIII 1.0.1, so enabling
  additional regionales later requires configuration only.
- **Answer integrity**: PASS. `AssistantAnswer`/`SearchResultSet` validation
  rules (data-model.md) require `context_sufficient = false` whenever no
  result carries a source URL, and the contract's `context_sufficient` /
  `sources` fields enforce the same rule at the API boundary (FR-005, revised
  2026-07-10; SC-002).
- **SDD phase discipline**: PASS. Only documentation artifacts were produced.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| None | N/A | N/A |

## Agent Context Update

The expected `.specify/scripts/powershell/update-agent-context.ps1` script is
not present in this repository. Agent context update was skipped without
modifying application code.
