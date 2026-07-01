"""
rag/domain/indexing.py — Index run and status domain models.

Traceability:
  IndexUpdateRun → FR-015, FR-016, FR-017, data-model.md §IndexUpdateRun
  IndexStatus    → FR-018, data-model.md §IndexStatus
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, Field, field_validator, model_validator

from rag.domain.enums import AreaInstitucional, EstadoIndexacion, ModoActualizacion


class FailureDetail(BaseModel):
    """Details of a single source/document failure recorded in an update run."""

    source_id: Optional[str] = Field(default=None)
    url: Optional[str] = Field(default=None)
    reason: str = Field(...)


class IndexUpdateRun(BaseModel):
    """An administrator-triggered index update operation.

    Mutable state machine: PENDIENTE → EN_PROCESO → COMPLETADO | FALLIDO.
    Only COMPLETADO runs may promote fragments to the active index (FR-016).

    data-model.md §IndexUpdateRun.
    """

    id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Unique run identifier.",
    )
    mode: ModoActualizacion = Field(..., description="Full rebuild or incremental.")
    selected_source_ids: list[str] = Field(
        default_factory=list,
        description="Required and non-empty for INCREMENTAL_SELECTED_SOURCES mode.",
    )
    status: EstadoIndexacion = Field(
        default=EstadoIndexacion.PENDIENTE,
        description="Current lifecycle state.",
    )
    started_at: Optional[datetime] = Field(default=None)
    finished_at: Optional[datetime] = Field(default=None)
    documents_seen: int = Field(default=0, ge=0)
    documents_indexed: int = Field(default=0, ge=0)
    documents_failed: int = Field(default=0, ge=0)
    fragments_indexed: int = Field(default=0, ge=0)
    failure_details: list[FailureDetail] = Field(default_factory=list)
    promoted: bool = Field(
        default=False,
        description="Whether this run became the active index.",
    )

    @model_validator(mode="after")
    def incremental_requires_sources(self) -> "IndexUpdateRun":
        if (
            self.mode == ModoActualizacion.INCREMENTAL_SELECTED_SOURCES
            and not self.selected_source_ids
        ):
            raise ValueError(
                "INCREMENTAL_SELECTED_SOURCES mode requires at least one "
                "selected_source_id (FR-015)"
            )
        return self

    @model_validator(mode="after")
    def failed_run_cannot_be_promoted(self) -> "IndexUpdateRun":
        if self.promoted and self.status == EstadoIndexacion.FALLIDO:
            raise ValueError("A FALLIDO run must not be promoted (FR-016)")
        return self

    # ------------------------------------------------------------------
    # State-transition methods
    # ------------------------------------------------------------------

    def start(self) -> None:
        """Transition PENDIENTE → EN_PROCESO."""
        if self.status != EstadoIndexacion.PENDIENTE:
            raise ValueError(
                f"Cannot start a run in state {self.status}; expected PENDIENTE"
            )
        self.status = EstadoIndexacion.EN_PROCESO
        self.started_at = datetime.now(timezone.utc)

    def complete(
        self,
        *,
        documents_indexed: int,
        documents_failed: int,
        fragments_indexed: int,
    ) -> None:
        """Transition EN_PROCESO → COMPLETADO with final counts (FR-017)."""
        if self.status != EstadoIndexacion.EN_PROCESO:
            raise ValueError(
                f"Cannot complete a run in state {self.status}; expected EN_PROCESO"
            )
        self.status = EstadoIndexacion.COMPLETADO
        self.documents_indexed = documents_indexed
        self.documents_failed = documents_failed
        self.fragments_indexed = fragments_indexed
        self.finished_at = datetime.now(timezone.utc)

    def fail(self, *, reason: str) -> None:
        """Transition EN_PROCESO → FALLIDO (FR-016)."""
        if self.status != EstadoIndexacion.EN_PROCESO:
            raise ValueError(
                f"Cannot fail a run in state {self.status}; expected EN_PROCESO"
            )
        self.status = EstadoIndexacion.FALLIDO
        self.finished_at = datetime.now(timezone.utc)
        self.failure_details.append(FailureDetail(reason=reason))

    def record_failure(self, *, source_id: str | None, url: str | None, reason: str) -> None:
        """Record an individual source/document failure without ending the run (FR-014)."""
        self.failure_details.append(
            FailureDetail(source_id=source_id, url=url, reason=reason)
        )
        self.documents_failed += 1


class IndexStatus(BaseModel):
    """Current state of the searchable corpus.

    data-model.md §IndexStatus.
    """

    ready: bool = Field(
        default=False,
        description="Whether query serving can use the index (FR-021).",
    )
    document_count: int = Field(default=0, ge=0)
    fragment_count: int = Field(default=0, ge=0)
    last_successful_update_at: Optional[datetime] = Field(default=None)
    covered_areas: list[AreaInstitucional] = Field(default_factory=list)
    covered_regionales: list[str] = Field(default_factory=list)
    recent_failures: list[FailureDetail] = Field(default_factory=list)
