# Tasks: Institutional Assistant

**Input**: Design documents from `/specs/001-institutional-assistant/`

**Prerequisites**: [plan.md](./plan.md), [spec.md](./spec.md), [research.md](./research.md), [data-model.md](./data-model.md), [contracts/openapi.yaml](./contracts/openapi.yaml), [quickstart.md](./quickstart.md)

**Scope rule**: Backend/RAG/API tasks are executable after this `tasks.md` is validated. Frontend phases are included because requested by the user, but they are blocked under the current spec because `spec.md` lists graphical web interface as out of scope and `plan.md` excludes frontend work. Do not execute frontend implementation tasks until `spec.md`, `plan.md`, contracts, and quickstart are amended.

**Tests**: Tests are mandatory for constitution-defined business rules: chunking overlap, semantic relevance ordering, RAG prompt context inclusion, scraper HTTP/empty-page handling, citation integrity, index preservation, and similarity-threshold refusal behavior.

**Organization**: Tasks are grouped in the requested phases, with backend first and frontend separated. Each task lists concrete file paths and dependencies.

## Format: `[ID] [P?] [Story?] Description`

- **[P]**: Can run in parallel after dependencies are complete because it touches different files.
- **[Story]**: Maps task to user stories from `spec.md` where applicable.
- Dependencies are listed in parentheses at the end of each task.

## Phase 1: Setup del Proyecto Backend (scraper, processor, API)

**Purpose**: Create project skeleton and configuration surfaces without implementing business logic.

- [X] T001 Create backend project metadata in `utn-assistant/pyproject.toml` with Python 3.11+, FastAPI, Pydantic v2, BeautifulSoup4, httpx, Playwright, sentence-transformers, ChromaDB, pytest, and pytest-mock dependencies (depends on none)
- [X] T002 Create backend package directories and `__init__.py` files in `utn-assistant/api/`, `utn-assistant/config/`, `utn-assistant/infra/`, `utn-assistant/processor/`, `utn-assistant/rag/`, `utn-assistant/scraper/`, `utn-assistant/vectorstore/`, and `utn-assistant/tests/` (depends on T001)
- [X] T003 [P] Create backend test directories in `utn-assistant/tests/unit/`, `utn-assistant/tests/integration/`, `utn-assistant/tests/contract/`, and `utn-assistant/tests/fixtures/html/` (depends on T002)
- [X] T004 [P] Create local environment template in `utn-assistant/.env.example` for source config path, ChromaDB path, Ollama URL, model names, thresholds, top_k, chunk sizing, request delay, and timeouts (depends on T002)
- [X] T005 [P] Create Docker Compose planning implementation files in `utn-assistant/infra/docker-compose.yml` and `utn-assistant/infra/README.md` for local ChromaDB, Ollama, API, scraper, and processor services (depends on T002)
- [X] T006 [P] Create central settings module skeleton in `utn-assistant/config/settings.py` and source configuration schema location in `utn-assistant/config/sources.example.yaml` (depends on T004)
- [X] T007 [P] Create API application entrypoint skeleton in `utn-assistant/api/main.py` and router package skeleton in `utn-assistant/api/routers/__init__.py` (depends on T002)
- [X] T008 [P] Create scraper package skeleton files in `utn-assistant/scraper/client.py`, `utn-assistant/scraper/robots.py`, `utn-assistant/scraper/extractor.py`, and `utn-assistant/scraper/run.py` (depends on T002)
- [X] T009 [P] Create processor package skeleton files in `utn-assistant/processor/text_cleaner.py`, `utn-assistant/processor/chunker.py`, `utn-assistant/processor/embeddings.py`, and `utn-assistant/processor/index_loader.py` (depends on T002)
- [X] T010 [P] Create RAG package skeleton files in `utn-assistant/rag/domain/__init__.py`, `utn-assistant/rag/services/__init__.py`, and `utn-assistant/rag/prompting.py` (depends on T002)

## Phase 2: Modelo de Dominio y Enums

**Purpose**: Define typed domain concepts and prioritize business-rule tests before service implementation.

- [X] T011 [P] [US1] Create failing unit tests for `UserQuery` validation in `utn-assistant/tests/unit/rag/domain/test_user_query.py` covering empty question, 2000-character limit, optional area, and max_results limit (depends on T003)
- [X] T012 [P] [US2] Create failing unit tests for context sufficiency and refusal rules in `utn-assistant/tests/unit/rag/domain/test_context_sufficiency.py` (depends on T003)
- [X] T013 [P] [US3] Create failing unit tests for citation integrity in `utn-assistant/tests/unit/rag/domain/test_citation_rules.py` requiring cited URLs to originate from retrieved fragments (depends on T003)
- [X] T014 [P] [US4] Create failing unit tests for index update state transitions in `utn-assistant/tests/unit/rag/domain/test_index_update_run.py` covering PENDIENTE, EN_PROCESO, COMPLETADO, FALLIDO, and promotion rules (depends on T003)
- [X] T015 [P] [US6] Create failing unit tests for area filter validation in `utn-assistant/tests/unit/rag/domain/test_area_filter.py` (depends on T003)
- [X] T016 Create enum definitions in `utn-assistant/rag/domain/enums.py` for AreaInstitucional, TipoFuente, EstadoIndexacion, and index update mode (depends on T011, T012, T013, T014, T015)
- [X] T017 [P] Create source and document domain models in `utn-assistant/rag/domain/sources.py` for InstitutionalSource and ExtractedDocument (depends on T016)
- [X] T018 [P] Create fragment and retrieval domain models in `utn-assistant/rag/domain/fragments.py` for ContentFragment, SearchResult, and SearchResultSet (depends on T016)
- [X] T019 [P] Create query and answer domain models in `utn-assistant/rag/domain/queries.py` for UserQuery, CitedSource, and AssistantAnswer (depends on T016)
- [X] T020 [P] Create index run and status domain models in `utn-assistant/rag/domain/indexing.py` for IndexUpdateRun and IndexStatus (depends on T016)
- [X] T021 Implement pure domain validation rules in `utn-assistant/rag/domain/rules.py` for context sufficiency, refusal text, citation validation, result ordering, and update promotion eligibility (depends on T017, T018, T019, T020)
- [X] T022 Update domain exports in `utn-assistant/rag/domain/__init__.py` for enums, models, and rules (depends on T016, T017, T018, T019, T020, T021)

## Phase 3: Persistencia en ChromaDB (colección, estrategia de re-indexación segura)

**Purpose**: Abstract vector persistence and safe index promotion before application services depend on it.

- [X] T023 [P] Create failing unit tests for vector search ordering in `utn-assistant/tests/unit/vectorstore/test_search_ordering.py` using fake repository results (depends on T018, T021)
- [X] T024 [P] Create failing integration tests for ChromaDB insert/search metadata filtering in `utn-assistant/tests/integration/vectorstore/test_chroma_repository.py` using a temporary persistence directory (depends on T003, T018)
- [X] T025 [P] Create failing unit tests for safe staging/swap index update behavior in `utn-assistant/tests/unit/vectorstore/test_index_staging.py` (depends on T020, T021)
- [X] T026 Create ChromaDB repository interface in `utn-assistant/vectorstore/repository.py` for upsert fragments, query fragments, delete collection, status, and health operations (depends on T018, T020)
- [X] T027 Implement ChromaDB PersistentClient adapter in `utn-assistant/vectorstore/chroma_repository.py` with one collection and metadata filters for area, regional, department, and source_type (depends on T006, T026)
- [X] T028 Implement index staging and promotion coordinator in `utn-assistant/vectorstore/index_manager.py` preserving the previous usable index on failed runs (depends on T020, T026, T027)
- [X] T029 Implement vectorstore health and status mapper in `utn-assistant/vectorstore/status.py` for IndexStatus fields (depends on T020, T027)
- [X] T030 Update vectorstore exports in `utn-assistant/vectorstore/__init__.py` (depends on T026, T027, T028, T029)

## Phase 4: Servicios de Aplicación (chunking, embeddings, pipeline RAG)

**Purpose**: Implement backend application services after domain rules and persistence contracts exist.

- [X] T031 [P] [US4] Create failing unit tests for text cleaning in `utn-assistant/tests/unit/processor/test_text_cleaner.py` covering HTML leftovers, scripts, navigation, and empty useful content (depends on T017)
- [X] T032 [P] [US4] Create failing unit tests for chunk size and overlap in `utn-assistant/tests/unit/processor/test_chunker.py` (depends on T018)
- [X] T033 [P] [US4] Create failing unit tests for embedding generation adapter behavior in `utn-assistant/tests/unit/processor/test_embeddings.py` with mocked sentence-transformers model (depends on T018)
- [X] T034 [P] [US1] Create failing unit tests for prompt context inclusion in `utn-assistant/tests/unit/rag/services/test_prompt_builder.py` (depends on T018, T019)
- [X] T035 [P] [US1] Create failing unit tests for answer orchestration in `utn-assistant/tests/unit/rag/services/test_responder_consulta_service.py` with mocked vectorstore and mocked Ollama client (depends on T021, T026)
- [X] T036 [P] [US4] Create failing unit tests for indexing orchestration in `utn-assistant/tests/unit/rag/services/test_indexar_contenido_service.py` (depends on T017, T018, T020, T028)
- [X] T037 Implement canonical text cleaner in `utn-assistant/processor/text_cleaner.py` for reusable normalization and empty-content rejection (depends on T031)
- [X] T038 Implement configurable chunker in `utn-assistant/processor/chunker.py` with default 800-unit chunk size and 120-unit overlap from settings (depends on T032, T037)
- [X] T039 Implement embeddings adapter in `utn-assistant/processor/embeddings.py` using configured sentence-transformers model name (depends on T033, T006)
- [X] T040 Implement index loader in `utn-assistant/processor/index_loader.py` to convert ExtractedDocument records into ContentFragment records and pass them to vectorstore staging (depends on T038, T039, T028)
- [X] T041 Implement robots-aware HTTP client in `utn-assistant/scraper/client.py` using configured delay, timeout, and source URL settings (depends on T006, T017)
- [X] T042 Implement robots.txt policy helper in `utn-assistant/scraper/robots.py` (depends on T041)
- [X] T043 Implement HTML extractor in `utn-assistant/scraper/extractor.py` for static pages and Playwright fallback when source requires JavaScript (depends on T037, T041, T042)
- [X] T044 Implement scraper orchestration in `utn-assistant/scraper/run.py` to produce ExtractedDocument records and per-source failures (depends on T017, T043)
- [X] T045 Implement prompt builder in `utn-assistant/rag/prompting.py` including retrieved context and citation metadata (depends on T034, T018, T019)
- [X] T046 Implement Ollama client adapter in `utn-assistant/rag/services/llm_client.py` with configurable URL, model, and generation timeout (depends on T006)
- [X] T047 [US1] Implement ResponderConsultaService in `utn-assistant/rag/services/responder_consulta.py` for retrieval, threshold validation, prompt construction, generation, and source return (depends on T021, T026, T045, T046)
- [X] T048 [US2] Implement insufficient-context response handling in `utn-assistant/rag/services/responder_consulta.py` using the approved refusal text (depends on T047)
- [X] T049 [US3] Implement source citation assembly in `utn-assistant/rag/services/responder_consulta.py` with URL and title when available (depends on T047)
- [X] T050 [US4] Implement IndexarContenidoService in `utn-assistant/rag/services/indexar_contenido.py` for full rebuild and incremental selected-source update flows (depends on T028, T040, T044)
- [X] T051 [US7] Implement ConsultarEstadoIndiceService in `utn-assistant/rag/services/consultar_estado_indice.py` (depends on T029)
- [X] T052 [US5] Implement dependency health service in `utn-assistant/rag/services/health.py` for ChromaDB, Ollama, and index readiness (depends on T029, T046)

## Phase 5: API REST

**Purpose**: Expose FastAPI contracts without placing business logic in routers.

- [X] T053 [P] [US1] Create failing contract tests for `POST /query` success response in `utn-assistant/tests/contract/api/test_query_contract.py` based on `specs/001-institutional-assistant/contracts/openapi.yaml` (depends on T047)
- [X] T054 [P] [US2] Create failing contract tests for `POST /query` insufficient-context response in `utn-assistant/tests/contract/api/test_query_refusal_contract.py` (depends on T048)
- [X] T055 [P] [US5] Create failing contract tests for query validation and dependency errors in `utn-assistant/tests/contract/api/test_error_contract.py` (depends on T052)
- [X] T056 [P] [US4] Create failing contract tests for `POST /index/rebuild` and `DELETE /index` in `utn-assistant/tests/contract/api/test_index_admin_contract.py` (depends on T050)
- [X] T057 [P] [US7] Create failing contract tests for `GET /index/status` and `GET /health` in `utn-assistant/tests/contract/api/test_status_health_contract.py` (depends on T051, T052)
- [X] T058 Create API DTOs in `utn-assistant/api/schemas.py` matching QueryRequest, QueryResponse, CitedSource, IndexStatus, IndexUpdateRequest, IndexUpdateRun, HealthResponse, and ErrorResponse (depends on T019, T020)
- [X] T059 Create dependency wiring in `utn-assistant/api/dependencies.py` for settings, vectorstore repository, application services, and admin operation guard (depends on T027, T047, T050, T051, T052)
- [X] T060 [US1] Implement query router in `utn-assistant/api/routers/query.py` delegating `POST /query` to ResponderConsultaService (depends on T053, T058, T059)
- [X] T061 [US5] Implement API error mapping in `utn-assistant/api/errors.py` for INVALID_QUESTION, INVALID_AREA, INDEX_NOT_READY, INDEX_EMPTY, GENERATOR_UNAVAILABLE, ADMIN_OPERATION_NOT_ALLOWED, UPDATE_REQUEST_INVALID, and TIMEOUT (depends on T055, T058)
- [X] T062 [US4] Implement index admin router in `utn-assistant/api/routers/index.py` for `GET /index/status`, `POST /index/rebuild`, and `DELETE /index` delegating to services (depends on T056, T057, T058, T059)
- [X] T063 [US5] Implement health router in `utn-assistant/api/routers/health.py` for `GET /health` delegating to health service (depends on T057, T058, T059)
- [X] T064 Wire routers, exception handlers, and app metadata in `utn-assistant/api/main.py` (depends on T060, T061, T062, T063)
- [X] T065 Update OpenAPI contract snapshot validation fixture in `utn-assistant/tests/contract/api/openapi.yaml` from `specs/001-institutional-assistant/contracts/openapi.yaml` (depends on T053, T054, T055, T056, T057)

## Phase 6: Tests Backend (incluye scraper)

**Purpose**: Complete backend verification for domain rules, services, scraper, vectorstore, contracts, and quickstart scenarios.

- [X] T066 [P] [US4] Create scraper fixture files in `utn-assistant/tests/fixtures/html/utn_valid_page.html`, `utn-assistant/tests/fixtures/html/utn_empty_page.html`, and `utn-assistant/tests/fixtures/html/utn_script_only_page.html` (depends on T043)
- [X] T067 [P] [US4] Implement scraper tests in `utn-assistant/tests/unit/scraper/test_extractor.py` for useful HTML, empty page discard, script-only discard, and title extraction (depends on T066)
- [X] T068 [P] [US4] Implement scraper HTTP failure tests in `utn-assistant/tests/unit/scraper/test_client_failures.py` for 404, 500, timeout, robots denial, and continuation behavior (depends on T041, T042)
- [X] T069 [P] [US4] Implement processor integration tests in `utn-assistant/tests/integration/processor/test_index_loader.py` for extracted document to fragment to staged vectorstore flow (depends on T040)
- [X] T070 [P] [US1] Implement RAG service integration tests in `utn-assistant/tests/integration/rag/test_query_success.py` using synthetic indexed fragments and mocked Ollama response (depends on T047, T049)
- [X] T071 [P] [US2] Implement RAG refusal integration tests in `utn-assistant/tests/integration/rag/test_query_refusal.py` for below-threshold and empty-result retrieval (depends on T048)
- [X] T072 [P] [US3] Implement citation integration tests in `utn-assistant/tests/integration/rag/test_citation_integrity.py` ensuring every cited source maps to retrieved context (depends on T049)
- [X] T073 [P] [US4] Implement safe re-indexing integration tests in `utn-assistant/tests/integration/indexing/test_safe_reindex.py` for failed run preserving previous index (depends on T050)
- [X] T074 [P] [US6] Implement area filter integration tests in `utn-assistant/tests/integration/rag/test_area_filtering.py` (depends on T047, T027)
- [X] T075 [P] [US5] Implement API dependency error integration tests in `utn-assistant/tests/integration/api/test_dependency_errors.py` (depends on T061, T063)
- [X] T076 [P] [US7] Implement index status performance test in `utn-assistant/tests/integration/api/test_index_status.py` asserting status fields and under-1-second target in local test conditions (depends on T062)
- [X] T077 [US1] Implement query response timing integration test in `utn-assistant/tests/integration/api/test_query_timing.py` for controlled local synthetic query path (depends on T060)
- [X] T078 Create backend test configuration in `utn-assistant/tests/conftest.py` with temporary ChromaDB path, fake sources, mocked Ollama client, and settings overrides (depends on T003, T006, T027, T046)
- [X] T079 Create backend test documentation in `utn-assistant/tests/README.md` mapping tests to spec FRs, user stories, and constitution business-rule requirements (depends on T066, T067, T068, T069, T070, T071, T072, T073, T074, T075, T076, T077, T078)

## Phase 7: Setup Frontend (bloqueado por spec actual)

**Purpose**: Record requested frontend setup work without authorizing implementation under the current spec.

- [ ] T080 BLOCKED: Amend `specs/001-institutional-assistant/spec.md` to remove graphical web interface from Out of Scope and add frontend user stories before creating `utn-assistant/frontend/package.json` (depends on validated decision to include frontend)
- [ ] T081 BLOCKED: Amend `specs/001-institutional-assistant/plan.md` to include React with Vite, TypeScript, CSS, frontend project structure, and Constitution Check impact before creating `utn-assistant/frontend/` (depends on T080)
- [ ] T082 BLOCKED: Amend `specs/001-institutional-assistant/contracts/openapi.yaml` or add frontend contract notes in `specs/001-institutional-assistant/contracts/frontend-contract.md` for query, index status, source display, and admin actions before frontend setup (depends on T081)
- [ ] T083 BLOCKED: Amend `specs/001-institutional-assistant/quickstart.md` with frontend validation scenarios before creating `utn-assistant/frontend/package.json`, `utn-assistant/frontend/index.html`, `utn-assistant/frontend/src/main.tsx`, and `utn-assistant/frontend/src/App.tsx` (depends on T082)
- [ ] T084 BLOCKED: After spec amendment, create frontend project metadata in `utn-assistant/frontend/package.json`, `utn-assistant/frontend/tsconfig.json`, `utn-assistant/frontend/vite.config.ts`, and `utn-assistant/frontend/src/main.tsx` (depends on T080, T081, T082, T083)
- [ ] T085 BLOCKED: After spec amendment, create frontend directories and base files in `utn-assistant/frontend/src/api/`, `utn-assistant/frontend/src/components/`, `utn-assistant/frontend/src/pages/`, `utn-assistant/frontend/src/styles.css`, and `utn-assistant/frontend/src/App.tsx` (depends on T084)

## Phase 8: Pantallas Frontend (bloqueado por spec actual)

**Purpose**: Record requested UI work as deferred until frontend scope is specified.

- [ ] T086 BLOCKED: After frontend spec amendment, create query page requirements-backed implementation in `utn-assistant/frontend/src/pages/QueryPage.tsx` and `utn-assistant/frontend/src/components/AreaSelect.tsx` (depends on T085 and frontend user story amendment)
- [ ] T087 BLOCKED: After frontend spec amendment, create answer/source display implementation in `utn-assistant/frontend/src/components/AnswerPanel.tsx` and `utn-assistant/frontend/src/components/SourceList.tsx` (depends on T086)
- [ ] T088 BLOCKED: After frontend spec amendment, create index status page implementation in `utn-assistant/frontend/src/pages/IndexStatusPage.tsx` and `utn-assistant/frontend/src/components/IndexStatusSummary.tsx` (depends on T085 and frontend admin story amendment)
- [ ] T089 BLOCKED: After frontend spec amendment, create frontend error and loading state components in `utn-assistant/frontend/src/components/ErrorMessage.tsx` and `utn-assistant/frontend/src/components/LoadingState.tsx` (depends on T085)
- [ ] T090 BLOCKED: After frontend spec amendment, create cited-source history view in `utn-assistant/frontend/src/pages/SourceHistoryPage.tsx` if added to spec scope (depends on T087 and frontend source-history story amendment)

## Phase 9: Integración Frontend-Backend (bloqueado por spec actual)

**Purpose**: Record requested integration work as deferred until frontend scope is specified.

- [ ] T091 BLOCKED: After frontend spec amendment, create API client in `utn-assistant/frontend/src/api/client.ts` for `POST /query`, `GET /index/status`, and `GET /health` based on `contracts/openapi.yaml` (depends on T084, T060, T062, T063)
- [ ] T092 BLOCKED: After frontend spec amendment, create frontend TypeScript DTOs in `utn-assistant/frontend/src/api/types.ts` matching QueryRequest, QueryResponse, CitedSource, IndexStatus, HealthResponse, and ErrorResponse (depends on T091)
- [ ] T093 BLOCKED: After frontend spec amendment, integrate query page with backend in `utn-assistant/frontend/src/pages/QueryPage.tsx` and `utn-assistant/frontend/src/api/client.ts` (depends on T086, T087, T091, T092)
- [ ] T094 BLOCKED: After frontend spec amendment, integrate status page with backend in `utn-assistant/frontend/src/pages/IndexStatusPage.tsx` and `utn-assistant/frontend/src/api/client.ts` (depends on T088, T091, T092)
- [ ] T095 BLOCKED: After frontend spec amendment, document frontend-backend local configuration in `utn-assistant/frontend/README.md` (depends on T093, T094)

## Phase 10: Validación End-to-End según quickstart.md

**Purpose**: Validate backend feature end-to-end against quickstart scenarios; include frontend validation only after frontend scope is amended and implemented.

- [X] T096 [US5] Create E2E validation checklist for health and empty index in `utn-assistant/tests/e2e/test_quickstart_health_empty_index.py` from `quickstart.md` Scenario 1 (depends on T064, T078)
- [X] T097 [US4] Create E2E validation checklist for full source update in `utn-assistant/tests/e2e/test_quickstart_full_update.py` from `quickstart.md` Scenario 2 (depends on T050, T062, T078)
- [X] T098 [US1] Create E2E validation checklist for successful query with citation in `utn-assistant/tests/e2e/test_quickstart_successful_query.py` from `quickstart.md` Scenario 3 (depends on T060, T070, T072, T078)
- [X] T099 [US2] Create E2E validation checklist for insufficient context refusal in `utn-assistant/tests/e2e/test_quickstart_refusal.py` from `quickstart.md` Scenario 4 (depends on T060, T071, T078)
- [X] T100 [US6] Create E2E validation checklist for area filtering in `utn-assistant/tests/e2e/test_quickstart_area_filtering.py` from `quickstart.md` Scenario 5 (depends on T060, T074, T078)
- [X] T101 [US4] Create E2E validation checklist for failed update preservation in `utn-assistant/tests/e2e/test_quickstart_failed_update.py` from `quickstart.md` Scenario 6 (depends on T050, T073, T078)
- [X] T102 [US5] Create E2E validation checklist for input and dependency errors in `utn-assistant/tests/e2e/test_quickstart_errors.py` from `quickstart.md` Scenario 7 (depends on T061, T075, T078)
- [X] T103 Create acceptance FAQ dataset documentation in `utn-assistant/tests/fixtures/acceptance/faq_dataset.md` for SC-001 representative institutional questions (depends on T079)
- [X] T104 Create validation report template in `utn-assistant/tests/e2e/validation_report.md` mapping quickstart outcomes to SC-001 through SC-008 (depends on T096, T097, T098, T099, T100, T101, T102, T103)
- [ ] T105 BLOCKED: After frontend spec amendment and implementation, create frontend E2E validation tasks in `utn-assistant/frontend/tests/e2e/quickstart.spec.ts` for query, area filter, status, loading, error, and source display flows (depends on T093, T094)

## Phase 11: Ajustes por revisión de alcance y citación (2026-07-10)

- [X] T106 Configurar `utn-assistant/config/sources.yaml` con únicamente fuentes UTN-FRBA Ing. en Sistemas (regional=FRBA); ninguna otra regional (FR-028) (depends on T006)
- [X] T107 Extraer del documento "Contexto Chatbot" las URLs oficiales de FRBA-Sistemas y cargarlas como fuentes WEB en `sources.yaml` con metadata area/regional (FR-011, FR-013) (depends on T106)
- [X] T108 [US3] Ajustar ResponderConsultaService en `utn-assistant/rag/services/responder_consulta.py`: si el contexto supera el umbral pero ningún fragmento recuperado tiene URL, devolver la respuesta de contexto insuficiente en lugar de una respuesta sin fuente (FR-005 rev.) (depends on T047, T049)
- [X] T109 [P] [US3] Test en `utn-assistant/tests/unit/rag/domain/test_citation_rules.py`: contexto suficiente sin ninguna URL en fragmentos → refusal; con al menos una URL → respuesta con fuente (FR-005 rev.) (depends on T108, T013)

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 Setup**: T001 -> T002 -> T003-T010.
- **Phase 2 Domain and Enums**: starts after T003; tests T011-T015 first, then T016-T022.
- **Phase 3 ChromaDB Persistence**: starts after domain models/rules T018-T021; T023-T025 first, then T026-T030.
- **Phase 4 Application Services**: starts after T017-T021 and T026-T030; tests T031-T036 first, then T037-T052.
- **Phase 5 API REST**: starts after services T047-T052; contract tests T053-T057 first, then T058-T065.
- **Phase 6 Backend Tests**: starts after relevant backend implementation tasks; can run broad integration work in parallel.
- **Phase 7-9 Frontend**: blocked until `spec.md`, `plan.md`, contracts, and quickstart are amended to bring frontend into scope.
- **Phase 10 E2E Validation**: backend E2E starts after T064 and T078; frontend E2E T105 remains blocked until frontend scope exists.

### User Story Dependencies

- **US1 Consulta institucional general**: requires setup, domain, vectorstore, RAG responder, query API, and successful query validation.
- **US2 Respuesta honesta**: depends on retrieval threshold rules and query API; can be implemented alongside US1 after domain rules exist.
- **US3 Indicacion de fuente**: depends on citation metadata in fragments and RAG responder; can be implemented alongside US1.
- **US4 Actualizacion del indice**: depends on scraper, processor, vectorstore staging, and index admin API.
- **US5 Disponibilidad y errores claros**: depends on API error mapping, health service, and dependency status checks.
- **US6 Filtro por area**: depends on metadata filtering in vectorstore and query service.
- **US7 Estado del indice**: depends on vectorstore status mapper and index API.

### Critical Path

T001 -> T002 -> T003 -> T011-T015 -> T016 -> T017-T022 -> T023-T030 -> T031-T036 -> T037-T052 -> T053-T065 -> T066-T079 -> T096-T104.

## Parallel Opportunities

- T003-T010 can run in parallel after T002.
- T011-T015 can run in parallel after T003.
- T017-T020 can run in parallel after T016.
- T023-T025 can run in parallel after domain rules exist.
- T031-T036 can run in parallel after their model dependencies exist.
- T041-T044 scraper tasks can progress in parallel with T045-T049 RAG tasks after shared domain/processor dependencies.
- T053-T057 contract tests can run in parallel after services exist.
- T066-T078 backend test tasks can run in parallel by test scope.
- T096-T103 E2E validation tasks can be prepared in parallel after API integration is stable.

## Parallel Example: Backend Domain and Rules

```bash
Task: "T011 Create failing unit tests for UserQuery validation in utn-assistant/tests/unit/rag/domain/test_user_query.py"
Task: "T012 Create failing unit tests for context sufficiency and refusal rules in utn-assistant/tests/unit/rag/domain/test_context_sufficiency.py"
Task: "T013 Create failing unit tests for citation integrity in utn-assistant/tests/unit/rag/domain/test_citation_rules.py"
Task: "T014 Create failing unit tests for index update state transitions in utn-assistant/tests/unit/rag/domain/test_index_update_run.py"
Task: "T015 Create failing unit tests for area filter validation in utn-assistant/tests/unit/rag/domain/test_area_filter.py"
```

## Parallel Example: Backend Integration Tests

```bash
Task: "T070 Implement RAG service integration tests in utn-assistant/tests/integration/rag/test_query_success.py"
Task: "T071 Implement RAG refusal integration tests in utn-assistant/tests/integration/rag/test_query_refusal.py"
Task: "T072 Implement citation integration tests in utn-assistant/tests/integration/rag/test_citation_integrity.py"
Task: "T074 Implement area filter integration tests in utn-assistant/tests/integration/rag/test_area_filtering.py"
```

## Implementation Strategy

### MVP First

1. Complete Phase 1 setup.
2. Complete Phase 2 domain/enums and mandatory business-rule tests.
3. Complete Phase 3 vectorstore persistence.
4. Complete the US1/US2/US3 subset of Phase 4 and Phase 5: T034, T035, T045, T046, T047, T048, T049, T053, T054, T058, T059, T060, T061, T064.
5. Validate with Phase 10 tasks T098 and T099.

### Incremental Delivery

1. Deliver query success with citations (US1 + US3).
2. Add insufficient-context refusal hardening (US2).
3. Add indexing/update administration and safe promotion (US4).
4. Add clear dependency and validation errors (US5).
5. Add area filtering (US6).
6. Add index status view through API (US7).
7. Revisit frontend only after spec amendment.

## Notes

- No task in this file should be executed before this `tasks.md` is reviewed and accepted.
- Frontend tasks T080-T095 and T105 are intentionally blocked under the current spec.
- Do not add user login, conversation history, PDF ingestion, SIU integration, paid external services, or automatic modified-page detection without amending `spec.md`.
- Keep API routers thin: endpoint files delegate to application services and contain no business logic.
- Keep ChromaDB access inside `utn-assistant/vectorstore/`; no other module imports ChromaDB directly.
