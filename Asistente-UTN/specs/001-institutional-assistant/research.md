# Research: Institutional Assistant

**Feature**: [spec.md](./spec.md)  
**Date**: 2026-06-30

## Decision: ChromaDB Collection Strategy

Use one persistent ChromaDB collection for the installation, with metadata
filters for `area`, `regional`, `department`, and `source_type`.

**Rationale**: A single collection simplifies global search when no area filter
is selected and keeps cross-regional installations manageable. Metadata filters
still support area-specific queries without duplicating collection management.

**Alternatives considered**:

- One collection per area: improves conceptual separation but complicates global
  search, status reporting, and future multi-area queries.
- One collection per regional: useful for strict tenant separation, but too much
  operational overhead for the initial local installation.

## Decision: Vector Similarity and Retrieval Limits

Use cosine similarity for semantic search. Retrieve a configurable `top_k`
number of fragments, default 5 and maximum 10 per user query.

**Rationale**: Cosine similarity matches common sentence embedding retrieval
practice. Limiting top_k keeps prompts bounded, supports the 5-second user
response target, and follows the meta-context constraint of at most 10
fragments per query.

**Alternatives considered**:

- Larger top_k values: can improve recall but increase prompt size and response
  latency.
- No maximum top_k: rejected because it makes cost, latency, and prompt quality
  unpredictable.

## Decision: Relevance Threshold

Use a configurable global relevance threshold with initial planning value
`0.65`. Area-specific thresholds are deferred.

**Rationale**: The spec clarified that the first version uses one global
threshold. `0.65` is a conservative initial value from the project context that
can be calibrated against an acceptance set before release.

**Alternatives considered**:

- Area-specific thresholds: useful later, but adds calibration complexity before
  enough area-specific evaluation data exists.
- No threshold: violates the requirement to refuse insufficient context.

## Decision: Chunk Size and Overlap

Use configurable chunk size and overlap. Initial planning defaults: 800 tokens
or equivalent text units per chunk, with 120 tokens overlap.

**Rationale**: Medium chunks preserve enough institutional context for
procedures and calendar answers while keeping retrieval focused. Overlap reduces
the chance of splitting important procedural details across fragments.

**Alternatives considered**:

- Very small chunks: improves precision but can lose procedural context.
- Very large chunks: improves context but can dilute relevance and slow prompt
  construction.
- Fixed non-configurable values: rejected by the constitution.

## Decision: Scraping Strategy

Use httpx plus BeautifulSoup4 for static public pages by default. Use Playwright
only for sources explicitly marked as JavaScript-dependent in source
configuration.

**Rationale**: Most institutional pages are expected to expose useful HTML
content without browser automation. Browser automation should be available but
not the default because it is slower and heavier.

**Alternatives considered**:

- Playwright for all pages: simpler behaviorally but slower and more resource
  intensive.
- Static-only scraping: insufficient for configured pages that require
  client-side rendering.

## Decision: robots.txt and Request Delay

Each source update must evaluate robots.txt rules and apply a configurable
delay between requests, default 1 second.

**Rationale**: This satisfies the constitution and reduces load on UTN servers.
The delay must remain configurable because different domains may publish
different crawl expectations.

**Alternatives considered**:

- No delay for local speed: rejected because it violates institutional crawling
  discipline.
- One hardcoded delay: rejected because operational values must live in
  configuration.

## Decision: Text Cleaning Ownership

Text cleaning belongs to `processor/text_cleaner` as a shared processing
concern. Scraper output may remove obvious non-content elements during
extraction, but canonical normalization is centralized in the processor layer.

**Rationale**: The constitution forbids duplicated text-cleaning logic. This
split allows scraping to discard scripts/nav while keeping normalization rules
reusable and testable.

**Alternatives considered**:

- Scraper-owned cleaning only: risks duplication when manual/PDF sources arrive
  later.
- RAG-owned cleaning: too late in the pipeline and mixes retrieval concerns with
  ingestion quality.

## Decision: Index Update Safety

Use a staging-and-swap model for complete rebuilds and selected-source
incremental updates: build new or updated fragments separately, validate the run
summary, then promote only after success. Failed runs preserve the previous
usable index.

**Rationale**: This directly supports the requirement that failed updates never
replace the last usable index and that active queries continue using the
previous index until a new load succeeds.

**Alternatives considered**:

- In-place update: simpler, but risks corrupting or partially replacing the
  usable index.
- Full rebuild only: conflicts with clarified incremental update scope.

## Decision: API Surface

Expose REST contracts for query, index status, full rebuild, index deletion, and
health. Administrator-only operations are documented as protected by local
operational controls in this version.

**Rationale**: These endpoints map directly to the spec. The contract documents
protected administrative actions without adding an end-user login feature, which
is out of scope.

**Alternatives considered**:

- CLI-only administration: satisfies some admin flows but makes status and
  operational checks less consistent with the meta context.
- Full authentication: deferred because end-user login and auth features are out
  of scope for the initial version.

## Decision: Timeout Strategy

Use configurable timeouts for source fetches, ChromaDB operations, and Ollama
generation. Initial planning defaults: 10 seconds per source fetch, 500 ms
target for vector search, and 30 seconds hard timeout for generation with a
controlled error response.

**Rationale**: The spec calls out controlled errors and a 5-second normal query
target, while the original context includes a 30-second generation timeout edge
case. Planning should separate normal SLOs from hard failure limits.

**Alternatives considered**:

- No hard timeout: risks hanging user queries.
- One timeout for all dependencies: too coarse for fetch, search, and generation
  with different performance characteristics.

## Decision: Frontend Scope

Do not plan frontend implementation for this feature. Keep frontend as future
meta-architecture context only.

**Rationale**: The active spec explicitly lists graphical web interface as out
of scope. Planning it now would violate traceability and the constitution.

**Alternatives considered**:

- Include React/Vite screens now: conflicts with `spec.md`.
- Add placeholder frontend tasks: rejected because tasks must trace to accepted
  feature scope.
