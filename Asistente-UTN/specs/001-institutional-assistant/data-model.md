# Data Model: Institutional Assistant

**Feature**: [spec.md](./spec.md)  
**Date**: 2026-06-30

## Enums and Closed Values

### AreaInstitucional

Allowed values:

- `ACADEMICA`
- `ADMINISTRATIVA`
- `BIENESTAR`
- `EXTENSION`

Validation rules:

- User area filters must be optional.
- When provided, area filters must match a configured value.
- Additional areas require configuration and typed representation before use.

### TipoFuente

Allowed values:

- `WEB`
- `PDF`
- `MANUAL`

Initial-version rule:

- Only `WEB` is in scope for ingestion.
- `PDF` and `MANUAL` are reserved for future versions and must not appear in
  initial ingestion runs except as rejected or inactive configuration values.

### EstadoIndexacion

Allowed values:

- `PENDIENTE`
- `EN_PROCESO`
- `COMPLETADO`
- `FALLIDO`

State rules:

- A run starts as `PENDIENTE`, moves to `EN_PROCESO`, and ends as `COMPLETADO`
  or `FALLIDO`.
- Only `COMPLETADO` runs can promote new indexed content.
- `FALLIDO` runs preserve the previous usable index.

## Entities

### InstitutionalSource

Represents a configured public UTN source.

Fields:

- `id`: stable identifier derived from configured source identity.
- `url`: public source URL.
- `title_hint`: optional configured source title.
- `area`: `AreaInstitucional`.
- `regional`: optional regional identifier or display name.
- `department`: optional department identifier or display name.
- `source_type`: `TipoFuente`, initial value `WEB`.
- `active`: whether this source participates in update runs.
- `requires_javascript`: whether extraction may use browser rendering.
- `crawl_delay_seconds`: optional per-source override.
- `include_patterns`: optional URL/content inclusion rules.
- `exclude_patterns`: optional URL/content exclusion rules.

Validation rules:

- `url` must be present and unique among active sources.
- `source_type` must be `WEB` for initial-version active sources.
- `area` must be one of the configured institutional areas.
- At least one of `regional` or rectorado-level identification must be known for
  multi-regional installations.

Relationships:

- One `InstitutionalSource` can produce many `ExtractedDocument` records.
- One `InstitutionalSource` can participate in many `IndexUpdateRun` records.

### ExtractedDocument

Represents useful text extracted from one configured source.

Fields:

- `id`: stable document identifier.
- `source_id`: reference to `InstitutionalSource`.
- `url`: final URL of the extracted page.
- `title`: page title when available.
- `raw_text`: extracted useful text before canonical processing.
- `clean_text`: normalized text after canonical cleaning.
- `area`: `AreaInstitucional`.
- `regional`: optional regional metadata.
- `department`: optional department metadata.
- `source_type`: `TipoFuente`.
- `extracted_at`: extraction timestamp.
- `status`: `EstadoIndexacion` or document processing status.
- `failure_reason`: optional failure detail.

Validation rules:

- Documents with empty, script-only, or navigation-only content are discarded or
  marked failed.
- `url`, `extracted_at`, `area`, and `source_type` are required for usable
  documents.
- `title` is stored when available for user-visible citations.

Relationships:

- One `ExtractedDocument` belongs to one `InstitutionalSource`.
- One `ExtractedDocument` produces many `ContentFragment` records.

### ContentFragment

Represents a searchable chunk of a document.

Fields:

- `id`: hash or stable key from source URL plus chunk offset/version.
- `document_id`: reference to `ExtractedDocument`.
- `text`: chunk text.
- `chunk_index`: ordinal position within the document.
- `start_offset`: optional start position in source text.
- `end_offset`: optional end position in source text.
- `embedding_model`: configured embedding model name.
- `metadata.url`: source URL.
- `metadata.title`: page title when available.
- `metadata.area`: `AreaInstitucional`.
- `metadata.regional`: optional regional metadata.
- `metadata.department`: optional department metadata.
- `metadata.source_type`: `TipoFuente`.
- `metadata.extraction_date`: document extraction date.
- `metadata.indexed_at`: index timestamp.

Validation rules:

- `text` must not be empty.
- Chunk size and overlap must match configured values.
- Metadata must be sufficient to cite URL and title when available.
- Fragment IDs must be stable for repeated processing of unchanged content.

Relationships:

- Many `ContentFragment` records belong to one `ExtractedDocument`.
- `SearchResult` references retrieved `ContentFragment` records.

### UserQuery

Represents a submitted question.

Fields:

- `question`: user question text.
- `area_filter`: optional `AreaInstitucional`.
- `submitted_at`: timestamp.
- `max_results`: optional requested result count bounded by configured maximum.

Validation rules:

- `question` must be non-empty after trimming.
- `question` must not exceed configured maximum length, initially 2000
  characters.
- `area_filter`, when present, must be configured.
- `max_results` must not exceed maximum retrieval count, initially 10.

Relationships:

- One `UserQuery` may produce one `AssistantAnswer`.
- One `UserQuery` may produce one `SearchResultSet`.

### SearchResult

Represents one retrieved fragment and its relevance.

Fields:

- `fragment_id`: reference to `ContentFragment`.
- `score`: semantic similarity score.
- `rank`: result order, starting at 1.
- `metadata`: citation and filtering metadata copied from the fragment.

Validation rules:

- Results must be ordered by descending relevance.
- Results below the configured threshold cannot authorize generation.
- Results must preserve source metadata for citation validation.

Relationships:

- Many `SearchResult` records can belong to one `SearchResultSet`.

### SearchResultSet

Represents the retrieval output for a query.

Fields:

- `query_id`: optional reference to `UserQuery`.
- `results`: ordered list of `SearchResult`.
- `context_sufficient`: whether at least one result meets the global threshold.
- `threshold`: global relevance threshold used.
- `area_filter`: optional `AreaInstitucional`.

Validation rules:

- `context_sufficient` is true only when at least one result meets or exceeds
  the threshold.
- Empty results always imply insufficient context.

### AssistantAnswer

Represents the user-visible answer or refusal.

Fields:

- `answer`: generated answer or approved refusal text.
- `sources`: list of `CitedSource`.
- `context_sufficient`: boolean.
- `error`: optional structured error code and message.

Validation rules:

- If `context_sufficient` is false, `answer` must use the approved refusal text:
  "No tengo informacion suficiente sobre este tema en las fuentes
  institucionales disponibles."
- If `context_sufficient` is true, `sources` must include at least one URL and
  title when available.
- The answer must not cite sources outside retrieved context.

### CitedSource

Represents source information shown to the user.

Fields:

- `url`: institutional source URL.
- `title`: page title when available.
- `area`: `AreaInstitucional`.
- `regional`: optional regional metadata.
- `department`: optional department metadata.

Validation rules:

- `url` is required.
- `title` is included when available.
- Every cited source must correspond to a retrieved `ContentFragment`.

### IndexUpdateRun

Represents an administrator-triggered update.

Fields:

- `id`: unique run identifier.
- `mode`: `FULL_REBUILD` or `INCREMENTAL_SELECTED_SOURCES`.
- `selected_source_ids`: required for incremental updates.
- `status`: `EstadoIndexacion`.
- `started_at`: start timestamp.
- `finished_at`: optional finish timestamp.
- `documents_seen`: count.
- `documents_indexed`: count.
- `documents_failed`: count.
- `fragments_indexed`: count.
- `failure_details`: list of source/document failures.
- `promoted`: whether the run became the active index.

Validation rules:

- Incremental updates require at least one selected configured source.
- Failed runs must not set `promoted` to true.
- A completed run must expose counts for indexed and failed items.

State transitions:

```text
PENDIENTE -> EN_PROCESO -> COMPLETADO -> promoted active index
PENDIENTE -> EN_PROCESO -> FALLIDO -> previous index remains active
```

### IndexStatus

Represents current searchable corpus health.

Fields:

- `ready`: whether query serving can use the index.
- `document_count`: current usable document count.
- `fragment_count`: current usable fragment count.
- `last_successful_update_at`: timestamp.
- `covered_areas`: list of `AreaInstitucional`.
- `covered_regionales`: list of configured regional metadata.
- `recent_failures`: list of recent failure summaries.

Validation rules:

- If `ready` is false, query responses must return a clear not-ready error.
- Status must be available without direct storage inspection.

## Cross-Entity Rules

- A generated answer requires a `SearchResultSet` with `context_sufficient =
  true`.
- Citation metadata must flow from `InstitutionalSource` to `ExtractedDocument`
  to `ContentFragment` to `AssistantAnswer`.
- Runtime search must use indexed fragments and vectorstore metadata, not full
  source documents in memory.
- A failed `IndexUpdateRun` must not change the active index visible to queries.
- Administrative operations are protected operationally in this version; end-user
  login is out of scope.
