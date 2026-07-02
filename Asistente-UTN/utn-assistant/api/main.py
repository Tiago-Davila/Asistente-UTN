"""
api/main.py — FastAPI application entrypoint.

Wires routers, exception handlers, and app metadata.
No business logic lives here — all logic is in routers/services.

Traceability: T064, tasks.md §Notes (keep routers thin).
"""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from api.errors import (
    AdminOperationNotAllowedError,
    GeneratorUnavailableError,
    IndexEmptyError,
    IndexNotReadyError,
    InvalidQuestionError,
    handle_admin_not_allowed,
    handle_generator_unavailable,
    handle_http_exception,
    handle_index_empty,
    handle_index_not_ready,
    handle_invalid_question,
    handle_validation_error,
)
from api.routers import query as query_router
from api.routers import index as index_router
from api.routers import health as health_router

# ---------------------------------------------------------------------------
# Application metadata
# ---------------------------------------------------------------------------
app = FastAPI(
    title="UTN Institutional Assistant",
    description=(
        "Local RAG service that answers natural-language questions in "
        "Argentinian Spanish from configured public UTN HTML sources."
    ),
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------
app.include_router(query_router.router)
app.include_router(index_router.router)
app.include_router(health_router.router)

# ---------------------------------------------------------------------------
# Exception handlers
# ---------------------------------------------------------------------------
app.add_exception_handler(InvalidQuestionError, handle_invalid_question)  # type: ignore[arg-type]
app.add_exception_handler(IndexNotReadyError, handle_index_not_ready)  # type: ignore[arg-type]
app.add_exception_handler(IndexEmptyError, handle_index_empty)  # type: ignore[arg-type]
app.add_exception_handler(GeneratorUnavailableError, handle_generator_unavailable)  # type: ignore[arg-type]
app.add_exception_handler(AdminOperationNotAllowedError, handle_admin_not_allowed)  # type: ignore[arg-type]
app.add_exception_handler(ValidationError, handle_validation_error)  # type: ignore[arg-type]

# FastAPI's built-in HTTPException handler is also overridden so that
# all error responses use the structured ErrorResponse envelope.
from fastapi.exceptions import HTTPException as FastAPIHTTPException
app.add_exception_handler(FastAPIHTTPException, handle_http_exception)  # type: ignore[arg-type]

# RequestValidationError from FastAPI (422 by default) → 400 with our envelope
from fastapi.exceptions import RequestValidationError

async def _handle_request_validation(request, exc: RequestValidationError):
    from api.errors import INVALID_QUESTION, INVALID_AREA, error_response
    errors = exc.errors()
    first = errors[0] if errors else {}
    field = ".".join(str(loc) for loc in first.get("loc", []))
    msg = first.get("msg", "Validation error")
    code = INVALID_AREA if "area" in field else INVALID_QUESTION
    return error_response(code, f"{field}: {msg}" if field else msg, status=400)

app.add_exception_handler(RequestValidationError, _handle_request_validation)  # type: ignore[arg-type]
