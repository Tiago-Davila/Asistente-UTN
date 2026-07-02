"""
api/routers/index.py — Index administration endpoints.

  GET  /index/status    → ConsultarEstadoIndiceService (US7)
  POST /index/rebuild   → IndexarContenidoService full/incremental (US4)
  DELETE /index         → repository.delete_collection (US4)

No business logic here — all logic lives in services.
Traceability: T062, US4, US7, tasks.md §Notes (keep routers thin).
"""
from __future__ import annotations

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from api.dependencies import (
    get_estado_indice_service,
    get_health_service,
    get_indexar_service,
    get_repository,
    get_settings_dep,
)
from api.schemas import (
    AdminOperationAccepted,
    IndexStatusResponse,
    IndexUpdateRequest,
    IndexUpdateRunResponse,
)
from config.settings import Settings
from rag.services.consultar_estado_indice import ConsultarEstadoIndiceService
from rag.services.indexar_contenido import IndexarContenidoService
from vectorstore.repository import VectorStoreRepository

logger = logging.getLogger(__name__)

router = APIRouter(tags=["index"])


@router.get(
    "/index/status",
    response_model=IndexStatusResponse,
    summary="Get current index status",
    operation_id="getIndexStatus",
)
def get_index_status(
    service: Annotated[ConsultarEstadoIndiceService, Depends(get_estado_indice_service)],
) -> IndexStatusResponse:
    """Return the current searchable corpus status (US7)."""
    status = service.get_status()
    return IndexStatusResponse(
        ready=status.ready,
        document_count=status.document_count,
        fragment_count=status.fragment_count,
        last_successful_update_at=status.last_successful_update_at,
        covered_areas=status.covered_areas,
        covered_regionales=status.covered_regionales,
        recent_failures=[
            {"source": f.source_id or "", "reason": f.reason}
            for f in status.recent_failures
        ],
    )


@router.post(
    "/index/rebuild",
    response_model=IndexUpdateRunResponse,
    status_code=202,
    summary="Start a full or selected-source index update",
    operation_id="rebuildIndex",
    responses={
        400: {"description": "Invalid update request"},
        403: {"description": "Administrative operation not allowed"},
    },
)
def rebuild_index(
    request: IndexUpdateRequest,
    service: Annotated[IndexarContenidoService, Depends(get_indexar_service)],
    settings: Annotated[Settings, Depends(get_settings_dep)],
) -> IndexUpdateRunResponse:
    """Trigger a full rebuild or incremental update (US4)."""
    from rag.domain.enums import ModoActualizacion
    from config.settings import get_settings

    # Load configured sources — in production these come from sources.yaml;
    # for this initial version we pass an empty list (real wiring in T078 conftest).
    sources: list = []
    try:
        from config.source_loader import load_sources
        sources = load_sources(settings.sources_config_path)
    except Exception:
        sources = []

    if request.mode == ModoActualizacion.INCREMENTAL_SELECTED_SOURCES:
        if not request.selected_source_ids:
            raise HTTPException(
                status_code=400,
                detail="selected_source_ids is required for INCREMENTAL_SELECTED_SOURCES mode",
            )
        run = service.incremental_update(
            sources=sources,
            selected_source_ids=request.selected_source_ids,
        )
    else:
        run = service.full_rebuild(sources=sources)

    return IndexUpdateRunResponse(
        run_id=run.id,
        mode=run.mode,
        status=run.status,
        started_at=run.started_at,
        finished_at=run.finished_at,
        documents_indexed=run.documents_indexed,
        documents_failed=run.documents_failed,
        fragments_indexed=run.fragments_indexed,
        promoted=run.promoted,
        failures=[
            {"source": f.source_id or "", "reason": f.reason}
            for f in run.failure_details
        ],
    )


@router.delete(
    "/index",
    response_model=AdminOperationAccepted,
    status_code=202,
    summary="Delete the current index",
    operation_id="deleteIndex",
    responses={
        403: {"description": "Administrative operation not allowed"},
    },
)
def delete_index(
    repository: Annotated[VectorStoreRepository, Depends(get_repository)],
) -> AdminOperationAccepted:
    """Delete all fragments from the active collection (US4)."""
    try:
        repository.delete_collection()
        return AdminOperationAccepted(
            accepted=True,
            message="El índice ha sido eliminado exitosamente.",
        )
    except Exception as exc:
        logger.error("Failed to delete index: %s", exc)
        raise HTTPException(status_code=500, detail="Error al eliminar el índice.") from exc
