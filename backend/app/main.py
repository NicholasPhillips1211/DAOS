import logging
import subprocess
import sys
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.core.config import settings
from app.core.error_handlers import register_error_handlers
from app.core.logging_middleware import RequestLoggingMiddleware
from app.core.security import SecurityHeadersMiddleware
from app import models  # noqa: F401

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)


@asynccontextmanager
async def lifespan(_: FastAPI):
    """Application lifespan hook.

    Alembic migrations are intentionally not run automatically in the app
    process to avoid multi-replica migration races and hidden failures in
    Kubernetes or other orchestrated environments. Run migrations separately
    (init container, CI job, or `python backend/scripts/run_migrations.py`).
    """

    yield



# During automated tests (pytest) we allow the application to import without
# requiring `API_KEYS_CSV` to be set. For real runs, fail fast when auth is
# enabled but no API keys are configured to avoid accidentally exposing the API.
if settings.auth_enabled and not settings.api_keys_csv and "pytest" not in sys.modules:
    raise RuntimeError("AUTH is enabled but `API_KEYS_CSV` / `api_keys_csv` is empty. Provide API keys or disable auth for local development.")

app = FastAPI(title=settings.app_name, lifespan=lifespan)

register_error_handlers(app)

app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Request-Id"],
)
if settings.enforce_security_headers:
    app.add_middleware(SecurityHeadersMiddleware)
app.include_router(api_router, prefix=settings.api_prefix)


@app.get("/")
def root() -> dict[str, str]:
    """Return a small health-style payload for quick runtime verification."""

    return {"name": settings.app_name, "environment": settings.environment}
