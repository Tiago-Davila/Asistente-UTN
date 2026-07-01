"""
api/errors.py — API error mapping and structured error responses.

Maps domain/service errors to the error codes defined in the OpenAPI
contract (contracts/openapi.yaml §ErrorDetail).

All error codes match the enum in the spec exactly so the API client
can handle them without parsing message text.

Traceability: T061, FR-021, US5, contracts/openapi.yaml §ErrorDetail.
"""
from __future__ import annotations

from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from api.schemas import ErrorDetail, ErrorResponse


# ---------------------------------------------------------------------------
# Error code constants (openapi.yaml §ErrorDetail enum)
# ---------------------------------------------------------------------------

INVALID_QUESTION = "INVALID_QUESTION"
INVALID_AREA = "INVALID_AREA"
INDEX_NOT_READY = "INDEX_NOT_READY"
INDEX_EMPTY = "INDEX_EMPTY"
GENERATOR_UNAVAILABLE = "GENERATOR_UNAVAILABLE"
ADMIN_OPERATION_NOT_ALLOWED = "ADMIN_OPERATION_NOT_ALLOWED"
UPDATE_REQUEST_INVALID = "UPDATE_REQUEST_INVALID"
TIMEOUT = "TIMEOUT"


# ---------------------------------------------------------------------------
# Domain exception types raised by services
# ---------------------------------------------------------------------------

class InvalidQuestionError(ValueError):
    """Question failed validation (empty, too long, blank)."""


class IndexNotReadyError(RuntimeError):
    """Index is not initialised or not ready to serve queries."""


class IndexEmptyError(RuntimeError):
    """Index exists but contains no fragments."""


class GeneratorUnavailableError(RuntimeError):
    """Local LLM (Ollama) is not reachable or timed out."""


class AdminOperationNotAllowedError(PermissionError):
    """Administrative operation attempted in a non-admin context."""


# ---------------------------------------------------------------------------
# Helper factories
# ---------------------------------------------------------------------------

def error_response(code: str, message: str, status: int = 400) -> JSONResponse:
    """Return a structured JSON error response."""
    payload = ErrorResponse(error=ErrorDetail(code=code, message=message))
    return JSONResponse(status_code=status, content=payload.model_dump())


# ---------------------------------------------------------------------------
# FastAPI exception handlers (registered in api/main.py)
# ---------------------------------------------------------------------------

async def handle_invalid_question(request: Request, exc: InvalidQuestionError) -> JSONResponse:
    return error_response(INVALID_QUESTION, str(exc), status=400)


async def handle_index_not_ready(request: Request, exc: IndexNotReadyError) -> JSONResponse:
    return error_response(INDEX_NOT_READY, str(exc), status=503)


async def handle_index_empty(request: Request, exc: IndexEmptyError) -> JSONResponse:
    return error_response(INDEX_EMPTY, str(exc), status=503)


async def handle_generator_unavailable(request: Request, exc: GeneratorUnavailableError) -> JSONResponse:
    return error_response(GENERATOR_UNAVAILABLE, str(exc), status=503)


async def handle_admin_not_allowed(request: Request, exc: AdminOperationNotAllowedError) -> JSONResponse:
    return error_response(ADMIN_OPERATION_NOT_ALLOWED, str(exc), status=403)


async def handle_validation_error(request: Request, exc: ValidationError) -> JSONResponse:
    """Handle Pydantic v2 validation errors from request body parsing."""
    first_error = exc.errors()[0] if exc.errors() else {}
    field = ".".join(str(loc) for loc in first_error.get("loc", []))
    msg = first_error.get("msg", "Validation error")
    code = INVALID_AREA if "area" in field else INVALID_QUESTION
    return error_response(code, f"{field}: {msg}" if field else msg, status=400)


async def handle_http_exception(request: Request, exc: HTTPException) -> JSONResponse:
    """Re-wrap FastAPI HTTPException into the structured error envelope."""
    code = INVALID_QUESTION
    if exc.status_code == 403:
        code = ADMIN_OPERATION_NOT_ALLOWED
    elif exc.status_code in (503, 502):
        code = GENERATOR_UNAVAILABLE
    return error_response(code, str(exc.detail), status=exc.status_code)
