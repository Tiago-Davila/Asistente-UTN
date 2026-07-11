# UTN Assistant — Test Suite Reference

**Traceability**: T079, T111  
**Feature**: [spec.md](../../specs/001-institutional-assistant/spec.md)  
**Date**: 2026-06-30 (revised 2026-07-10)

This document maps every test file to the spec FRs, user stories, and
constitution business rules it validates.

**2026-07-10 revision**: FR-005 was revised so that threshold-sufficient
context with no citable source URL among retrieved fragments falls back to
the insufficient-context refusal (see `test_citation_rules.py` and
`integration/rag/test_query_refusal.py`). FR-027/FR-028 scope the current
corpus to UTN-FRBA, Ingenieria en Sistemas only; SC-002 was revised and
SC-009 added accordingly (see `config/sources.yaml`, FR-028).

---

## Directory Layout

```
tests/
├── conftest.py                          # Shared fixtures (T078)
├── unit/
│   ├── rag/
│   │   ├── domain/                      # Domain model + rules
│   │   └── services/                    # Application services
│   ├── processor/                       # Text cleaning, chunking, embeddings
│   ├── scraper/                         # Scraper client + extractor
│   └── vectorstore/                     # Search ordering + staging
├── integration/
│   ├── rag/                             # RAG service integration
│   ├── processor/                       # Index loader integration
│   ├── indexing/                        # Safe re-indexing
│   ├── vectorstore/                     # ChromaDB adapter
│   └── api/                             # API integration + timing
├── contract/
│   └── api/                             # HTTP contract tests
├── fixtures/
│   ├── html/                            # Scraper HTML fixtures
│   └── acceptance/                      # FAQ acceptance dataset
└── e2e/                                 # End-to-end validation
```

---

## Mapping: Tests → FRs / User Stories / Business Rules

### Unit Tests — Domain

| File | FRs | Stories | Business Rules |
|------|-----|---------|----------------|
| `unit/rag/domain/test_user_query.py` | FR-002 | US1 | Question validation: non-empty, ≤2000 chars, area optional, max_results ≤10 |
| `unit/rag/domain/test_context_sufficiency.py` | FR-006, FR-007 | US2 | Threshold refusal; exact refusal text |
| `unit/rag/domain/test_citation_rules.py` | FR-005, FR-005 rev., FR-008 | US3 | Citations from retrieved fragments only; title when available; threshold-sufficient context without a citable URL → refusal (T109) |
| `unit/rag/domain/test_index_update_run.py` | FR-016, FR-017 | US4 | State machine; only COMPLETADO promotes; counts required |
| `unit/rag/domain/test_area_filter.py` | FR-009, FR-010 | US6 | All 4 areas valid; invalid string rejected; no filter searches all |

### Unit Tests — Processor

| File | FRs | Stories | Business Rules |
|------|-----|---------|----------------|
| `unit/processor/test_text_cleaner.py` | FR-012 | US4 | Remove scripts, nav, footer; normalise whitespace; empty detection |
| `unit/processor/test_chunker.py` | FR-022 | US4 | Chunk size and overlap configurable; sequential indices |
| `unit/processor/test_embeddings.py` | FR-022 | US4 | Lazy-loads configured model; encode returns float lists |

### Unit Tests — Scraper

| File | FRs | Stories | Business Rules |
|------|-----|---------|----------------|
| `unit/scraper/test_extractor.py` | FR-012 | US4 | Useful text extracted; empty/script-only → empty; title extracted |
| `unit/scraper/test_client_failures.py` | FR-014, FR-023 | US4 | 404/500/timeout/robots → error; continuation without stopping |

### Unit Tests — RAG Services

| File | FRs | Stories | Business Rules |
|------|-----|---------|----------------|
| `unit/rag/services/test_prompt_builder.py` | FR-003, FR-004, FR-005, FR-008 | US1 | Context included; AR-Spanish instruction; no-invent directive; URL in prompt |
| `unit/rag/services/test_responder_consulta_service.py` | FR-003, FR-005, FR-006, FR-007, FR-009 | US1, US2, US3 | Answer with sources; refusal; LLM not called on refusal; area filter forwarded |
| `unit/rag/services/test_indexar_contenido_service.py` | FR-015, FR-016, FR-017 | US4 | Full rebuild COMPLETADO; failure → abort; incremental filters sources |

### Unit Tests — Vectorstore

| File | FRs | Stories | Business Rules |
|------|-----|---------|----------------|
| `unit/vectorstore/test_search_ordering.py` | FR-003 | US1 | Results ordered by descending relevance; rank assigned from 1 |
| `unit/vectorstore/test_index_staging.py` | FR-015, FR-016 | US4 | Staging buffer; FALLIDO abort preserves active index |

### Integration Tests

| File | FRs | Stories | Business Rules |
|------|-----|---------|----------------|
| `integration/vectorstore/test_chroma_repository.py` | FR-003, FR-009, FR-013, FR-019 | US1, US6 | Real ChromaDB; area filter; upsert idempotent; delete |
| `integration/processor/test_index_loader.py` | FR-013, FR-015 | US4 | Document → fragments → staging; metadata flows; unusable doc skipped |
| `integration/rag/test_query_success.py` | FR-003, FR-005 | US1, US3 | Real ChromaDB + mocked LLM; answer + citation returned |
| `integration/rag/test_query_refusal.py` | FR-005 rev., FR-006, FR-007 | US2 | Below-threshold and empty-index refusal; exact text; LLM not called; relevant context with no citable URL → refusal (T110) |
| `integration/rag/test_citation_integrity.py` | FR-005, FR-008 | US3 | Cited URLs from retrieved context only; context_sufficient ↔ sources non-empty |
| `integration/indexing/test_safe_reindex.py` | FR-016 | US4 | Failed run does not replace active index; previous index queryable after failure |
| `integration/rag/test_area_filtering.py` | FR-009, FR-010 | US6 | Area filter restricts to selected area; EXTENSION empty → refusal |
| `integration/api/test_dependency_errors.py` | FR-021 | US5 | Service error payload → 503; no internal details in message |
| `integration/api/test_index_status.py` | FR-018 | US7 | Status fields present; response < 1 second (SC-004) |
| `integration/api/test_query_timing.py` | SC-004 | US1 | Query response < 5 seconds in controlled test conditions |

### Contract Tests

| File | FRs | Stories | Business Rules |
|------|-----|---------|----------------|
| `contract/api/test_query_contract.py` | FR-001, FR-002, FR-005, FR-009 | US1 | 200 on success; required fields; area filter accepted; validation → 400 |
| `contract/api/test_query_refusal_contract.py` | FR-006, FR-007 | US2 | 200 with refusal text; context_sufficient=false; empty sources |
| `contract/api/test_error_contract.py` | FR-002, FR-021 | US5 | INVALID_QUESTION code; structured error envelope; 503 for dependency errors |
| `contract/api/test_index_admin_contract.py` | FR-015, FR-017, FR-019 | US4 | 202 rebuild; run_id/status/counts; incremental requires IDs; 202 delete |
| `contract/api/test_status_health_contract.py` | FR-018, FR-021 | US5, US7 | Status fields; health chromadb/ollama/index_ready; degraded when down |

---

## Constitution Business Rules Coverage

| Business Rule | Test(s) |
|---------------|---------|
| Chunk overlap | `unit/processor/test_chunker.py` |
| Semantic relevance ordering | `unit/vectorstore/test_search_ordering.py`, `integration/vectorstore/test_chroma_repository.py` |
| RAG prompt context inclusion | `unit/rag/services/test_prompt_builder.py` |
| Scraper HTTP/empty-page handling | `unit/scraper/test_client_failures.py`, `unit/scraper/test_extractor.py` |
| Citation integrity | `unit/rag/domain/test_citation_rules.py`, `integration/rag/test_citation_integrity.py` |
| Index preservation on failure | `unit/vectorstore/test_index_staging.py`, `integration/indexing/test_safe_reindex.py` |
| Similarity-threshold refusal | `unit/rag/domain/test_context_sufficiency.py`, `integration/rag/test_query_refusal.py` |
| Citable-source refusal (FR-005 rev. 2026-07-10) | `unit/rag/domain/test_citation_rules.py::TestCitableSourcePresence`, `integration/rag/test_query_refusal.py::TestQueryRefusalNoCitableSource` |
| FRBA-only corpus scope (FR-027/FR-028) | `config/sources.yaml` (only `regional` referring to UTN-FRBA is configured); acceptance validation via SC-009 in `validation_report.md` |

---

## Running Tests

```bash
# All tests
python -m pytest tests/

# Unit tests only (fast, no ChromaDB)
python -m pytest tests/unit/

# Integration tests
python -m pytest tests/integration/

# Contract tests
python -m pytest tests/contract/
```
