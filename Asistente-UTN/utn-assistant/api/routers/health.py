"""
api/routers/health.py — Health check endpoint.

  GET /health → HealthService (US5)

No business logic here — delegates entirely to HealthService.
Traceability: T063, US5, tasks.md §Notes (keep routers thin).
"""
from __future__ import annotations

import logging
from typing import Annotated

from fastapi import APIRouter, Depends

from api.dependencies import get_health_service
from api.schemas import HealthResponse
from rag.services.health import HealthService, HealthStatus

logger = logging.getLogger(__name__)

router = APIRouter(tags=["health"])


def _map_status(hs: HealthStatus) -> str:
    """Convert a HealthStatus to the contract status string."""
    if hs.chromadb_healthy and hs.ollama_healthy and hs.index_ready:
        return "ok"
    if hs.chromadb_healthy or hs.ollama_healthy:
        return "degraded"
    return "unavailable"


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Check local dependency readiness",
    operation_id="getHealth",
)
def get_health(
    service: Annotated[HealthService, Depends(get_health_service)],
) -> HealthResponse:
    """Return readiness status of ChromaDB, Ollama, and the index (US5)."""
    hs = service.check()
    return HealthResponse(
        status=_map_status(hs),
        chromadb="ok" if hs.chromadb_healthy else "unavailable",
        ollama="ok" if hs.ollama_healthy else "unavailable",
        index_ready=hs.index_ready,
    )
