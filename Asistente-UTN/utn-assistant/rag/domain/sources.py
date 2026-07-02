"""
rag/domain/sources.py — Source and document domain models.

Traceability:
  InstitutionalSource → FR-011, FR-013, FR-022, FR-023, FR-027,
                        data-model.md §InstitutionalSource
  ExtractedDocument   → FR-012, FR-013, FR-014,
                        data-model.md §ExtractedDocument
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, Field, field_validator, model_validator

from rag.domain.enums import AreaInstitucional, EstadoIndexacion, TipoFuente


class InstitutionalSource(BaseModel):
    """A configured public UTN source eligible for extraction.

    data-model.md §InstitutionalSource.
    """

    id: str = Field(..., description="Stable identifier derived from source identity.")
    url: str = Field(..., description="Public source URL.")
    title_hint: Optional[str] = Field(
        default=None, description="Optional configured source title."
    )
    area: AreaInstitucional = Field(
        ..., description="Institutional area this source belongs to."
    )
    regional: Optional[str] = Field(
        default=None,
        description="Regional name or identifier (e.g. 'Regional Buenos Aires').",
    )
    department: Optional[str] = Field(
        default=None, description="Optional department name."
    )
    source_type: TipoFuente = Field(
        default=TipoFuente.WEB,
        description="Source ingestion type; WEB only in v1.",
    )
    active: bool = Field(
        default=True, description="Whether this source participates in update runs."
    )
    requires_javascript: bool = Field(
        default=False,
        description="True if extraction may need browser rendering (Playwright).",
    )
    crawl_delay_seconds: Optional[float] = Field(
        default=None,
        ge=0.0,
        description="Per-source crawl delay override (seconds).",
    )
    include_patterns: list[str] = Field(
        default_factory=list,
        description="Optional URL/content inclusion rules.",
    )
    exclude_patterns: list[str] = Field(
        default_factory=list,
        description="Optional URL/content exclusion rules.",
    )

    @field_validator("url")
    @classmethod
    def url_must_not_be_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("url must not be empty")
        return v

    @field_validator("source_type")
    @classmethod
    def active_sources_must_be_web(cls, v: TipoFuente) -> TipoFuente:
        # Validation that active sources must have source_type WEB is enforced
        # at the model_validator level where active is also available.
        return v

    @model_validator(mode="after")
    def active_source_must_be_web(self) -> "InstitutionalSource":
        if self.active and self.source_type != TipoFuente.WEB:
            raise ValueError(
                f"Active sources must have source_type WEB in v1; got {self.source_type}"
            )
        return self


class ExtractedDocument(BaseModel):
    """Useful institutional text extracted from one configured source.

    data-model.md §ExtractedDocument.
    """

    id: str = Field(..., description="Stable document identifier.")
    source_id: str = Field(..., description="Reference to InstitutionalSource.id.")
    url: str = Field(..., description="Final URL of the extracted page.")
    title: Optional[str] = Field(
        default=None, description="Page title when available."
    )
    raw_text: str = Field(
        default="", description="Extracted useful text before canonical processing."
    )
    clean_text: str = Field(
        default="", description="Normalized text after canonical cleaning."
    )
    area: AreaInstitucional = Field(..., description="Institutional area.")
    regional: Optional[str] = Field(default=None)
    department: Optional[str] = Field(default=None)
    source_type: TipoFuente = Field(default=TipoFuente.WEB)
    extracted_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Extraction timestamp.",
    )
    status: EstadoIndexacion = Field(default=EstadoIndexacion.PENDIENTE)
    failure_reason: Optional[str] = Field(default=None)

    @field_validator("url")
    @classmethod
    def url_must_not_be_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("url must not be empty")
        return v

    def is_usable(self) -> bool:
        """Return True if the document has non-empty clean text and is not failed."""
        return (
            bool(self.clean_text.strip())
            and self.status != EstadoIndexacion.FALLIDO
        )
