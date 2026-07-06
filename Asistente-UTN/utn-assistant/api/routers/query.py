"""
api/routers/query.py — POST /query and POST /query/stream endpoints.

Delegates entirely to ResponderConsultaService — no business logic here.
Validates the request body and maps domain results to API schemas.

Traceability: T060, US1, US2, US3, tasks.md §Notes (keep routers thin).
"""
from __future__ import annotations

import json
import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import ValidationError

from api.dependencies import get_responder_service
from api.errors import (
    INVALID_AREA,
    INVALID_QUESTION,
    InvalidQuestionError,
    error_response,
)
from api.schemas import (
    CitedSourceResponse,
    ErrorDetail,
    QueryRequest,
    QueryResponse,
)
from rag.domain.queries import UserQuery
from rag.services.responder_consulta import ResponderConsultaService

logger = logging.getLogger(__name__)

router = APIRouter(tags=["query"])


@router.post(
    "/query",
    response_model=QueryResponse,
    responses={
        400: {"description": "Invalid question or filter"},
        503: {"description": "Index or generation dependency unavailable"},
    },
    summary="Answer an institutional question",
    operation_id="queryAssistant",
)
def query_assistant(
    request: QueryRequest,
    service: Annotated[ResponderConsultaService, Depends(get_responder_service)],
) -> QueryResponse:
    """Accept a natural-language question and return a grounded answer.

    Returns the approved refusal text when context is insufficient (US2).
    Includes source URL and title when available (US3).
    """
    # Build domain query — validation already done by QueryRequest
    try:
        domain_query = UserQuery(
            question=request.question,
            area_filter=request.area,
            max_results=request.max_results,
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    # Delegate to service
    answer = service.answer(domain_query)

    # If service returned a structural error payload, propagate as 503
    if answer.error:
        code = answer.error.get("code", "GENERATOR_UNAVAILABLE")
        message = answer.error.get("message", "Servicio no disponible.")
        return JSONResponse(
            status_code=503,
            content={
                "error": {"code": code, "message": message},
                "answer": "",
                "context_sufficient": False,
                "sources": [],
            },
        )

    # Map domain sources to API schema
    sources = [
        CitedSourceResponse(
            url=s.url,
            title=s.title,
            area=s.area,
            regional=s.regional,
            department=s.department,
        )
        for s in answer.sources
    ]

    return QueryResponse(
        answer=answer.answer,
        context_sufficient=answer.context_sufficient,
        sources=sources,
    )


@router.post(
    "/query/stream",
    responses={
        400: {"description": "Invalid question or filter"},
        503: {"description": "Index or generation dependency unavailable"},
    },
    summary="Answer an institutional question with token streaming",
    operation_id="queryAssistantStream",
)
def query_assistant_stream(
    request: QueryRequest,
    service: Annotated[ResponderConsultaService, Depends(get_responder_service)],
) -> StreamingResponse:
    """Like POST /query but streams the answer as Server-Sent Events (SSE).

    Each event is a JSON object on a ``data:`` line:

    - ``data: {"chunk": "..."}`` — a successive text chunk during generation.
    - ``data: {"done": true, "context_sufficient": bool, "sources": [...], "error": null}``
      — final event signalling completion with source metadata.

    Clients should read the stream until the ``done`` event is received.
    """
    try:
        domain_query = UserQuery(
            question=request.question,
            area_filter=request.area,
            max_results=request.max_results,
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    def event_generator():
        for event in service.stream_answer(domain_query):
            yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",  # disable Nginx buffering if proxied
        },
    )
