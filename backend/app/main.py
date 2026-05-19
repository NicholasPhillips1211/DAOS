import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from alembic import command
from alembic.config import Config

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

    Running Alembic at startup ensures schema changes are versioned and applied
    consistently instead of relying on create_all behavior.
    """

    alembic_cfg = Config(str(Path(__file__).resolve().parents[1] / "alembic.ini"))
    command.upgrade(alembic_cfg, "head")
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
