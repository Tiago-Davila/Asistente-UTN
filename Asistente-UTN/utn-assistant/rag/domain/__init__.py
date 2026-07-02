"""
rag/domain — Domain model and business rules package.

Public API — import from here rather than from sub-modules directly.

Enums:
  AreaInstitucional, TipoFuente, EstadoIndexacion, ModoActualizacion

Source/document models:
  InstitutionalSource, ExtractedDocument

Fragment/retrieval models:
  FragmentMetadata, ContentFragment, SearchResult, SearchResultSet

Query/answer models:
  UserQuery, CitedSource, AssistantAnswer

Index run/status models:
  FailureDetail, IndexUpdateRun, IndexStatus

Rules (pure functions):
  REFUSAL_TEXT
  is_context_sufficient, make_refusal_answer
  validate_citation_integrity, build_cited_sources
  order_results, can_promote
"""
from __future__ import annotations

# -- Enums ------------------------------------------------------------------
from rag.domain.enums import (
    AreaInstitucional,
    EstadoIndexacion,
    ModoActualizacion,
    TipoFuente,
)

# -- Source / document models -----------------------------------------------
from rag.domain.sources import (
    ExtractedDocument,
    InstitutionalSource,
)

# -- Fragment / retrieval models --------------------------------------------
from rag.domain.fragments import (
    ContentFragment,
    FragmentMetadata,
    SearchResult,
    SearchResultSet,
)

# -- Query / answer models --------------------------------------------------
from rag.domain.queries import (
    AssistantAnswer,
    CitedSource,
    UserQuery,
)

# -- Index run / status models ----------------------------------------------
from rag.domain.indexing import (
    FailureDetail,
    IndexStatus,
    IndexUpdateRun,
)

# -- Rules (pure functions) -------------------------------------------------
from rag.domain import rules
from rag.domain.rules import (
    REFUSAL_TEXT,
    build_cited_sources,
    can_promote,
    is_context_sufficient,
    make_refusal_answer,
    order_results,
    validate_citation_integrity,
)

__all__ = [
    # enums
    "AreaInstitucional",
    "EstadoIndexacion",
    "ModoActualizacion",
    "TipoFuente",
    # source / document
    "InstitutionalSource",
    "ExtractedDocument",
    # fragment / retrieval
    "FragmentMetadata",
    "ContentFragment",
    "SearchResult",
    "SearchResultSet",
    # query / answer
    "UserQuery",
    "CitedSource",
    "AssistantAnswer",
    # index run / status
    "FailureDetail",
    "IndexUpdateRun",
    "IndexStatus",
    # rules
    "rules",
    "REFUSAL_TEXT",
    "is_context_sufficient",
    "make_refusal_answer",
    "validate_citation_integrity",
    "build_cited_sources",
    "order_results",
    "can_promote",
]
