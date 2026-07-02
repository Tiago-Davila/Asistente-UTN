---

description: "Task list template for feature implementation"
---

# Tasks: [FEATURE NAME]

**Input**: Design documents from `/specs/[###-feature-name]/`

**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Tests are mandatory for constitution-defined business rules touched by the feature: chunking overlap, semantic relevance ordering, RAG prompt context inclusion, scraper HTTP/empty-page handling, and similarity-threshold refusal behavior. Other tests are included when required by the feature specification or risk profile.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions
- Include requirement or decision traceability when the task is not directly tied to a user story

## Path Conventions

- `src/api/`: FastAPI endpoints, DTOs, validation only
- `src/config/`: `settings.py` and typed configuration
- `src/scraper/`: UTN content acquisition and initial cleanup
- `src/processor/`: chunking, embeddings, vectorstore loading
- `src/vectorstore/`: ChromaDB persistence and semantic search abstraction
- `src/rag/`: retrieval, prompt orchestration, answer generation
- `tests/unit/`, `tests/integration/`, `tests/contract/`: tests by scope

<!--
  ============================================================================
  IMPORTANT: The tasks below are SAMPLE TASKS for illustration purposes only.

  The /speckit-tasks command MUST replace these with actual tasks based on:
  - User stories from spec.md (with their priorities P1, P2, P3...)
  - Feature requirements from plan.md
  - Entities from data-model.md
  - Endpoints from contracts/
  - Constitution-required business-rule tests for touched behavior

  Tasks MUST be organized by user story so each story can be:
  - Implemented independently
  - Tested independently
  - Delivered as an MVP increment

  DO NOT keep these sample tasks in the generated tasks.md file.
  ============================================================================
-->

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Create constitution-aligned project structure under src/ and tests/
- [ ] T002 Initialize Python 3.11+ project with FastAPI, BeautifulSoup4, Playwright, sentence-transformers, ChromaDB, Ollama client, and pytest dependencies
- [ ] T003 [P] Configure linting, formatting, and typing tools
- [ ] T004 [P] Create central settings module in src/config/settings.py for URLs, models, thresholds, delays, chunk settings, and persistence paths

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**CRITICAL**: No user story work can begin until this phase is complete

Examples of foundational tasks (adjust based on your project):

- [ ] T005 Define Enums/constants for institutional areas, source types, and indexing states
- [ ] T006 Create base DTOs/entities and metadata contracts used across layers
- [ ] T007 Setup API routing and dependency injection without business logic in endpoints
- [ ] T008 Setup ChromaDB persistence configuration and vectorstore test fixture
- [ ] T009 Setup Ollama and ChromaDB Docker Compose services with persistent volumes
- [ ] T010 Setup error handling and structured logging

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - [Title] (Priority: P1) MVP

**Goal**: [Brief description of what this story delivers]

**Independent Test**: [How to verify this story works on its own]

### Tests for User Story 1

> **NOTE: Write required tests FIRST and ensure they FAIL before implementation.**

- [ ] T011 [P] [US1] Contract test for [endpoint] in tests/contract/test_[name].py
- [ ] T012 [P] [US1] Integration test for [user journey] in tests/integration/test_[name].py
- [ ] T013 [P] [US1] Unit test for constitution-required rule [chunking/search/RAG/scraper/threshold] in tests/unit/test_[name].py

### Implementation for User Story 1

- [ ] T014 [P] [US1] Create/update domain model or DTO in src/[layer]/[file].py
- [ ] T015 [US1] Implement service logic in the appropriate non-API layer
- [ ] T016 [US1] Implement FastAPI endpoint or interface adapter in src/api/[file].py
- [ ] T017 [US1] Add validation and error handling
- [ ] T018 [US1] Add source metadata handling where retrieved institutional content is used

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - [Title] (Priority: P2)

**Goal**: [Brief description of what this story delivers]

**Independent Test**: [How to verify this story works on its own]

### Tests for User Story 2

- [ ] T019 [P] [US2] Contract or integration test for [behavior] in tests/[scope]/test_[name].py
- [ ] T020 [P] [US2] Unit test for constitution-required rule [if touched] in tests/unit/test_[name].py

### Implementation for User Story 2

- [ ] T021 [P] [US2] Create/update model or DTO in src/[layer]/[file].py
- [ ] T022 [US2] Implement service logic in the appropriate non-API layer
- [ ] T023 [US2] Implement endpoint/interface adapter in src/api/[file].py
- [ ] T024 [US2] Integrate with User Story 1 components if needed while preserving independent testability

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - [Title] (Priority: P3)

**Goal**: [Brief description of what this story delivers]

**Independent Test**: [How to verify this story works on its own]

### Tests for User Story 3

- [ ] T025 [P] [US3] Contract or integration test for [behavior] in tests/[scope]/test_[name].py
- [ ] T026 [P] [US3] Unit test for constitution-required rule [if touched] in tests/unit/test_[name].py

### Implementation for User Story 3

- [ ] T027 [P] [US3] Create/update model or DTO in src/[layer]/[file].py
- [ ] T028 [US3] Implement service logic in the appropriate non-API layer
- [ ] T029 [US3] Implement endpoint/interface adapter in src/api/[file].py

**Checkpoint**: All user stories should now be independently functional

---

[Add more user story phases as needed, following the same pattern]

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] TXXX [P] Documentation updates in docs/
- [ ] TXXX Code cleanup and refactoring
- [ ] TXXX Performance optimization across retrieval/indexing paths
- [ ] TXXX [P] Additional tests for edge cases and regression risks in tests/
- [ ] TXXX Validate no hardcoded URLs, model names, thresholds, delays, or persistence paths remain outside configuration
- [ ] TXXX Validate no runtime semantic search scans full documents in memory
- [ ] TXXX Run quickstart.md validation

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
  - User stories can then proceed in parallel if staffed
  - Or sequentially in priority order (P1 -> P2 -> P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - no dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - may integrate with US1 but remains independently testable
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - may integrate with US1/US2 but remains independently testable

### Within Each User Story

- Required tests MUST be written and FAIL before implementation
- Models/DTOs before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel within Phase 2
- Once Foundational phase completes, user stories can start in parallel if capacity allows
- Tests for a user story marked [P] can run in parallel
- Models/DTOs within a story marked [P] can run in parallel

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together:
Task: "Contract test for [endpoint] in tests/contract/test_[name].py"
Task: "Integration test for [user journey] in tests/integration/test_[name].py"
Task: "Unit test for [constitution-required rule] in tests/unit/test_[name].py"

# Launch independent models/DTOs for User Story 1 together:
Task: "Create [DTO] in src/api/[dto].py"
Task: "Create [domain model] in src/[layer]/[model].py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. STOP and VALIDATE: Test User Story 1 independently
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational -> Foundation ready
2. Add User Story 1 -> Test independently -> Deploy/Demo
3. Add User Story 2 -> Test independently -> Deploy/Demo
4. Add User Story 3 -> Test independently -> Deploy/Demo
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1
   - Developer B: User Story 2
   - Developer C: User Story 3
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Required tests must fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, business logic in API endpoints, hardcoded operational values, untraced components
