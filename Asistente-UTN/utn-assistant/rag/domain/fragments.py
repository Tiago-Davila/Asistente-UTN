"""
rag/domain/fragments.py — Fragment and retrieval domain models.

Traceability:
  ContentFragment  → FR-003, FR-005, FR-013, data-model.md §ContentFragment
  SearchResult     → data-model.md §SearchResult
  SearchResultSet  → FR-006, FR-010, data-model.md §SearchResultSet
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

from pydantic import BaseModel, Field, field_validator

from rag.domain.enums import AreaInstitucional, TipoFuente


class FragmentMetadata(BaseModel):
    """Metadata stored alongside a ContentFragment in the vector index.

    Must be sufficient to cite URL and title when available (FR-005).
    data-model.md §ContentFragment metadata fields.
    """

    url: str = Field(..., description="Source URL.")
    title: Optional[str] = Field(default=None, description="Page title when available.")
    area: AreaInstitucional = Field(..., description="Institutional area.")
    regional: Optional[str] = Field(default=None)
    department: Optional[str] = Field(default=None)
    source_type: TipoFuente = Field(default=TipoFuente.WEB)
    extraction_date: Optional[datetime] = Field(default=None)
    indexed_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )


class ContentFragment(BaseModel):
    """A searchable chunk of an extracted document.

    data-model.md §ContentFragment.
    """

    id: str = Field(
        ...,
        description="Stable key derived from source URL + chunk offset/version.",
    )
    document_id: str = Field(..., description="Reference to ExtractedDocument.id.")
    text: str = Field(..., description="Chunk text.")
    chunk_index: int = Field(..., ge=0, description="Ordinal position within the document.")
    start_offset: Optional[int] = Field(default=None)
    end_offset: Optional[int] = Field(default=None)
    embedding_model: str = Field(
        ..., description="Configured embedding model name used to produce this fragment."
    )
    metadata: FragmentMetadata = Field(..., description="Citation and filtering metadata.")

    @field_validator("text")
    @classmethod
    def text_must_not_be_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("ContentFragment text must not be empty")
        return v


class SearchResult(BaseModel):
    """One retrieved fragment and its relevance score.

    data-model.md §SearchResult.
    """

    fragment_id: str = Field(..., description="Reference to ContentFragment.id.")
    score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Cosine similarity score (0–1).",
    )
    rank: int = Field(..., ge=1, description="Result rank, starting at 1.")
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Citation and filtering metadata copied from the fragment.",
    )

    def meets_threshold(self, threshold: float) -> bool:
        """Return True if this result's score meets or exceeds the threshold."""
        return self.score >= threshold


class SearchResultSet(BaseModel):
    """The retrieval output for a single query.

    data-model.md §SearchResultSet.
    """

    query_id: Optional[str] = Field(default=None)
    results: list[SearchResult] = Field(default_factory=list)
    context_sufficient: bool = Field(
        default=False,
        description=(
            "True only when at least one result meets or exceeds the threshold."
        ),
    )
    threshold: float = Field(
        default=0.65,
        ge=0.0,
        le=1.0,
        description="Global relevance threshold used for this query.",
    )
    area_filter: Optional[AreaInstitucional] = Field(default=None)

    def urls(self) -> list[str]:
        """Return unique source URLs from all results."""
        seen: set[str] = set()
        out: list[str] = []
        for r in self.results:
            url = r.metadata.get("url")
            if url and url not in seen:
                seen.add(url)
                out.append(url)
        return out
