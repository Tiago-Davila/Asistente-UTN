"""
api/schemas.py — API DTOs (Data Transfer Objects).

Pydantic v2 models matching the OpenAPI contract in
specs/001-institutional-assistant/contracts/openapi.yaml.

These are pure API-layer shapes. Domain models live in rag/domain/.
The schemas reference domain enums directly for consistency.

Traceability: T058, contracts/openapi.yaml.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field, field_validator

from rag.domain.enums import AreaInstitucional, EstadoIndexacion, ModoActualizacion


# ---------------------------------------------------------------------------
# Request schemas
# ---------------------------------------------------------------------------

class QueryRequest(BaseModel):
    """POST /query request body — openapi.yaml §QueryRequest."""

    question: str = Field(..., min_length=1, max_length=2000)
    area: Optional[AreaInstitucional] = Field(
        default=None,
        description="Optional institutional area filter.",
    )
    max_results: Optional[int] = Field(
        default=None, ge=1, le=10,
        description="Maximum fragments to retrieve (1–10).",
    )

    @field_validator("question")
    @classmethod
    def question_not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("question must not be blank")
        return v


class IndexUpdateRequest(BaseModel):
    """POST /index/rebuild request body — openapi.yaml §IndexUpdateRequest."""

    mode: ModoActualizacion
    selected_source_ids: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------

class CitedSourceResponse(BaseModel):
    """A single cited source in a query response — openapi.yaml §CitedSource."""

    url: str
    title: Optional[str] = None
    area: Optional[AreaInstitucional] = None
    regional: Optional[str] = None
    department: Optional[str] = None


class ErrorDetail(BaseModel):
    """Structured error detail — openapi.yaml §ErrorDetail."""

    code: str
    message: str


class ErrorResponse(BaseModel):
    """Top-level error envelope — openapi.yaml §ErrorResponse."""

    error: ErrorDetail


class QueryResponse(BaseModel):
    """POST /query response body — openapi.yaml §QueryResponse."""

    answer: str
    context_sufficient: bool
    sources: list[CitedSourceResponse] = Field(default_factory=list)
    error: Optional[ErrorDetail] = None


class IndexStatusResponse(BaseModel):
    """GET /index/status response body — openapi.yaml §IndexStatus."""

    ready: bool
    document_count: int = 0
    fragment_count: int = 0
    last_successful_update_at: Optional[datetime] = None
    covered_areas: list[AreaInstitucional] = Field(default_factory=list)
    covered_regionales: list[str] = Field(default_factory=list)
    recent_failures: list[dict] = Field(default_factory=list)


class IndexUpdateRunResponse(BaseModel):
    """POST /index/rebuild response body — openapi.yaml §IndexUpdateRun."""

    run_id: str
    mode: ModoActualizacion
    status: EstadoIndexacion
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    documents_indexed: int = 0
    documents_failed: int = 0
    fragments_indexed: int = 0
    promoted: bool = False
    failures: list[dict] = Field(default_factory=list)


class AdminOperationAccepted(BaseModel):
    """DELETE /index response body — openapi.yaml §AdminOperationAccepted."""

    accepted: bool
    message: str


class HealthResponse(BaseModel):
    """GET /health response body — openapi.yaml §HealthResponse."""

    status: str  # ok | degraded | unavailable
    chromadb: str  # ok | unavailable
    ollama: str  # ok | unavailable
    index_ready: bool = False


class StreamChunk(BaseModel):
    """One event in a POST /query/stream SSE response.

    Two shapes are emitted:

    - Text chunk during generation: ``{"chunk": "..."}``
    - Final completion event: ``{"done": true, "context_sufficient": bool,
      "sources": [...], "error": null | {...}}``
    """

    chunk: Optional[str] = None
    done: Optional[bool] = None
    context_sufficient: Optional[bool] = None
    sources: Optional[list[CitedSourceResponse]] = None
    error: Optional[ErrorDetail] = None
