"""
rag/domain/rules.py — Pure domain validation rules.

This module contains only pure functions that implement business rules.
No infrastructure imports (ChromaDB, httpx, FastAPI, etc.) belong here.

Traceability:
  is_context_sufficient  → FR-006, data-model.md §SearchResultSet
  has_citable_source     → FR-005 (rev. 2026-07-10), data-model.md §SearchResultSet
  REFUSAL_TEXT           → FR-007
  make_refusal_answer    → FR-007
  validate_citation_integrity → FR-005, FR-008, data-model.md §CitedSource
  build_cited_sources    → FR-005
  order_results          → data-model.md §SearchResult (descending relevance)
  can_promote            → FR-016, data-model.md §EstadoIndexacion
"""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from rag.domain.fragments import SearchResult, SearchResultSet
    from rag.domain.indexing import IndexUpdateRun
    from rag.domain.queries import AssistantAnswer, CitedSource

# ---------------------------------------------------------------------------
# FR-007: Approved refusal text — exact and immutable.
# ---------------------------------------------------------------------------

REFUSAL_TEXT: str = (
    "No tengo informacion suficiente sobre este tema "
    "en las fuentes institucionales disponibles."
)


# ---------------------------------------------------------------------------
# Context sufficiency (FR-006, data-model.md §SearchResultSet)
# ---------------------------------------------------------------------------

def is_context_sufficient(result_set: "SearchResultSet") -> bool:
    """Return True when at least one result meets or exceeds the threshold.

    Empty results always return False.
    """
    if not result_set.results:
        return False
    return any(r.score >= result_set.threshold for r in result_set.results)


# ---------------------------------------------------------------------------
# Citable source presence (FR-005, revised 2026-07-10)
# ---------------------------------------------------------------------------

def has_citable_source(result_set: "SearchResultSet") -> bool:
    """Return True when at least one retrieved fragment carries a source URL.

    FR-005 (revised 2026-07-10): if retrieved context clears the relevance
    threshold but no retrieved fragment carries a source URL, the system
    must not produce an uncited answer. Callers must treat this as
    insufficient context and fall back to the approved refusal instead.
    """
    return bool(result_set.urls())


# ---------------------------------------------------------------------------
# Refusal answer factory (FR-007)
# ---------------------------------------------------------------------------

def make_refusal_answer() -> "AssistantAnswer":
    """Return an AssistantAnswer using the approved refusal text.

    The model validator in AssistantAnswer enforces the exact text when
    context_sufficient is False and error is None, so we set answer
    directly to REFUSAL_TEXT.
    """
    from rag.domain.queries import AssistantAnswer

    # Bypass the validator that checks consistency — we are constructing
    # the canonical refusal object so values are definitionally correct.
    return AssistantAnswer(
        answer=REFUSAL_TEXT,
        sources=[],
        context_sufficient=False,
    )


# ---------------------------------------------------------------------------
# Citation integrity (FR-005, FR-008)
# ---------------------------------------------------------------------------

def validate_citation_integrity(
    cited: list["CitedSource"],
    results: list["SearchResult"],
) -> bool:
    """Return True when every cited URL originates from a retrieved fragment.

    Special case: empty citations with empty results → True (refusal path).
    Empty citations with non-empty results → False (missing required citations).
    """
    if not results:
        # Refusal path — no sources expected.
        return len(cited) == 0

    if not cited:
        # Results exist but no citations provided — violation of FR-005.
        return False

    retrieved_urls: set[str] = {
        r.metadata.get("url", "") for r in results if r.metadata.get("url")
    }
    return all(c.url in retrieved_urls for c in cited)


def build_cited_sources(results: list["SearchResult"]) -> list["CitedSource"]:
    """Build deduplicated CitedSource list from retrieved SearchResult objects.

    Preserves page title when available (FR-005).
    Deduplicates by URL — uses the first occurrence's metadata.
    """
    from rag.domain.queries import CitedSource
    from rag.domain.enums import AreaInstitucional

    seen: set[str] = set()
    cited: list[CitedSource] = []

    for r in results:
        url = r.metadata.get("url")
        if not url or url in seen:
            continue
        seen.add(url)

        # Safely coerce area metadata to enum or None.
        raw_area = r.metadata.get("area")
        area: AreaInstitucional | None = None
        if raw_area is not None:
            try:
                area = AreaInstitucional(raw_area)
            except ValueError:
                area = None

        cited.append(
            CitedSource(
                url=url,
                title=r.metadata.get("title"),
                area=area,
                regional=r.metadata.get("regional"),
                department=r.metadata.get("department"),
            )
        )

    return cited


# ---------------------------------------------------------------------------
# Result ordering (data-model.md §SearchResult: descending relevance)
# ---------------------------------------------------------------------------

def order_results(results: list["SearchResult"]) -> list["SearchResult"]:
    """Return results sorted by descending score, re-ranked from 1."""
    sorted_results = sorted(results, key=lambda r: r.score, reverse=True)
    for idx, result in enumerate(sorted_results, start=1):
        result.rank = idx
    return sorted_results


# ---------------------------------------------------------------------------
# Update promotion eligibility (FR-016, data-model.md §EstadoIndexacion)
# ---------------------------------------------------------------------------

def can_promote(run: "IndexUpdateRun") -> bool:
    """Return True only when the run has status COMPLETADO.

    Failed, in-progress, or pending runs must not replace the active index.
    """
    from rag.domain.enums import EstadoIndexacion

    return run.status == EstadoIndexacion.COMPLETADO
