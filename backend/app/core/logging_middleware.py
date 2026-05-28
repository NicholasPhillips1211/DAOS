"""ASGI middleware for request-level structured logging and correlation IDs.

Every request receives a unique ``X-Request-Id`` header so operators and
frontend error handlers can trace failures back to a specific backend event.
"""

from __future__ import annotations

import logging
import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from app.core.observability import observability_store

logger = logging.getLogger("daos.requests")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Attach a correlation ID, log timing, and propagate the ID on the response."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id

        start = time.perf_counter()
        response = await call_next(request)
        elapsed_ms = round((time.perf_counter() - start) * 1000, 1)

        response.headers["X-Request-Id"] = request_id

        logger.info(
            "method=%s path=%s status=%s duration_ms=%s request_id=%s",
            request.method,
            request.url.path,
            response.status_code,
            elapsed_ms,
            request_id,
        )

        observability_store.record_request(
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            duration_ms=elapsed_ms,
        )

        return response
