"""Global exception handlers that produce a consistent JSON error envelope.

Every error response uses the shape ``{"error": {"code": ..., "message": ..., "details": ...}}``
so the frontend can parse structured feedback instead of guessing from status codes alone.
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger("daos.errors")


def _build_envelope(code: str, message: str, details: list[Any] | None = None) -> dict[str, Any]:
    """Return the canonical error object that all handlers emit."""

    body: dict[str, Any] = {"code": code, "message": message}
    if details:
        body["details"] = details
    return {"error": body}


async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    """Handle explicit HTTPException raises from route or service code."""

    request_id = getattr(request.state, "request_id", None)
    logger.warning("http_error status=%s detail=%s request_id=%s", exc.status_code, exc.detail, request_id)

    return JSONResponse(
        status_code=exc.status_code,
        content=_build_envelope(f"http_{exc.status_code}", str(exc.detail)),
        headers={"X-Request-Id": request_id} if request_id else {},
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Handle Pydantic / FastAPI request-validation failures with field-level detail."""

    request_id = getattr(request.state, "request_id", None)
    field_errors = [
        {"field": " -> ".join(str(loc) for loc in err.get("loc", [])), "message": err.get("msg", "")}
        for err in exc.errors()
    ]
    logger.warning("validation_error fields=%d request_id=%s", len(field_errors), request_id)

    return JSONResponse(
        status_code=422,
        content=_build_envelope("validation_error", "Request validation failed", field_errors),
        headers={"X-Request-Id": request_id} if request_id else {},
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Catch-all for unexpected errors so the client always gets structured JSON."""

    request_id = getattr(request.state, "request_id", None)
    logger.exception("unhandled_error request_id=%s", request_id)

    return JSONResponse(
        status_code=500,
        content=_build_envelope("internal_error", "An unexpected error occurred"),
        headers={"X-Request-Id": request_id} if request_id else {},
    )


def register_error_handlers(app: FastAPI) -> None:
    """Wire all global exception handlers onto the application."""

    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)
