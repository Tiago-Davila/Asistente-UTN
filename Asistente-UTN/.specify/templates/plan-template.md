# Implementation Plan: [FEATURE]

**Branch**: `[###-feature-name]` | **Date**: [DATE] | **Spec**: [link]

**Input**: Feature specification from `/specs/[###-feature-name]/spec.md`

**Note**: This template is filled in by the `/speckit-plan` command. See `.specify/templates/plan-template.md` for the execution workflow.

## Summary

[Extract from feature spec: primary requirement + technical approach from research]

## Technical Context

<!--
  ACTION REQUIRED: Replace the content in this section with the technical details
  for the project. The defaults below reflect the project constitution.
-->

**Language/Version**: Python 3.11+ or NEEDS CLARIFICATION

**Primary Dependencies**: FastAPI, BeautifulSoup4, Playwright, sentence-transformers, ChromaDB, Ollama API client or NEEDS CLARIFICATION

**Storage**: Local persistent ChromaDB, Docker volumes for Ollama models, files as needed or NEEDS CLARIFICATION

**Testing**: pytest or NEEDS CLARIFICATION

**Target Platform**: Local Docker Compose environment or NEEDS CLARIFICATION

**Project Type**: Python RAG web service with scraper/processor workers or NEEDS CLARIFICATION

**Performance Goals**: [Domain-specific latency, indexing, or retrieval goals or NEEDS CLARIFICATION]

**Constraints**: 100% local runtime, no paid external core services, RAG queries stateless by default (conversation history is opt-in per session, ephemeral with configurable TTL, and never a knowledge source), robots.txt compliance, configured request delays or NEEDS CLARIFICATION

**Scale/Scope**: [Regional/departments/content volume expected for this feature or NEEDS CLARIFICATION]

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Traceability**: Every planned component maps to a user story,
  functional requirement, or documented decision. No untraced code.
- **Layer separation**: Scraping, processing, vectorstore, RAG orchestration,
  and FastAPI endpoints remain in their constitution-defined layers.
- **Configuration**: URLs, model names, thresholds, delays, chunk settings, and
  persistence options are centralized in `config/settings.py` or typed
  equivalent.
- **Closed values**: Institutional areas, source types, and indexing states use
  Enums/constants rather than loose strings.
- **Local-only stack**: The plan uses Python 3.11+, BeautifulSoup4, Playwright,
  sentence-transformers `paraphrase-multilingual-mpnet-base-v2`, persistent
  local ChromaDB, Ollama, FastAPI, and Docker Compose. No paid external core
  service.
- **Business-rule tests**: Tests are planned for relevant chunking overlap,
  semantic relevance ordering, prompt context inclusion, scraper HTTP/empty-page
  handling, and similarity-threshold refusal behavior.
- **Search scalability**: Runtime semantic search uses ChromaDB/vectorstore, not
  full-document in-memory scans.
- **Answer integrity**: Responses are in Argentinian Spanish, cite institutional
  sources when available, and refuse insufficient context below threshold.
- **SDD phase discipline**: This plan produces Markdown artifacts only; no
  application code, tests, executable config, or infrastructure is written
  before validated `tasks.md`.

## Project Structure

### Documentation (this feature)

```text
specs/[###-feature]/
├── plan.md              # This file (/speckit-plan command output)
├── research.md          # Phase 0 output (/speckit-plan command)
├── data-model.md        # Phase 1 output (/speckit-plan command)
├── quickstart.md        # Phase 1 output (/speckit-plan command)
├── contracts/           # Phase 1 output (/speckit-plan command)
└── tasks.md             # Phase 2 output (/speckit-tasks command - NOT created by /speckit-plan)
```

### Source Code (repository root)

<!--
  ACTION REQUIRED: Replace the placeholder tree below with the concrete layout
  for this feature. Keep constitution-defined layer boundaries intact.
-->

```text
src/
├── api/             # FastAPI endpoints, DTOs, input/output validation
├── config/          # settings.py and typed configuration
├── processor/       # chunking, embeddings, vectorstore loading
├── rag/             # retrieval + prompt orchestration + answer generation
├── scraper/         # UTN content acquisition and initial cleanup
└── vectorstore/     # ChromaDB persistence and semantic search abstraction

tests/
├── contract/
├── integration/
└── unit/
```

**Structure Decision**: [Document the selected structure and reference the real
directories captured above]

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| [e.g., extra abstraction over ChromaDB] | [current need] | [why direct adapter is insufficient] |
| [e.g., temporary in-memory list in tests] | [specific problem] | [why vectorstore fixture is not enough] |
