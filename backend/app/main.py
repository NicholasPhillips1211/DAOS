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
    """Apply database migrations on startup and keep shutdown minimal.

    We invoke Alembic through the project's Python environment as a subprocess
    to avoid import-time conflicts with the local `backend/alembic` package.
    If Alembic is unavailable or the call fails, fall back to leaving the
    schema management to test fixtures or manual setup.
    """

    backend_dir = Path(__file__).resolve().parents[1]
    try:
        subprocess.run([sys.executable, "-m", "alembic", "upgrade", "head"], check=True, cwd=str(backend_dir))
    except Exception:
        logging.warning("Alembic upgrade failed or not available; skipping automatic migrations.")
    yield


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
