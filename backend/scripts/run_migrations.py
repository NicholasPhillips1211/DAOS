"""Run Alembic migrations using the Python API.

Usage:
  python backend/scripts/run_migrations.py

This script is intended for use in init containers or CI so the web process
does not attempt to run migrations at import/startup time.
"""
from __future__ import annotations

from alembic.config import Config
from alembic import command
from pathlib import Path
import logging
import sys

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("daos.migrations")


def main() -> int:
    backend_dir = Path(__file__).resolve().parents[1]
    alembic_ini = backend_dir / "alembic.ini"
    if not alembic_ini.exists():
        logger.error("alembic.ini not found at %s", alembic_ini)
        return 2

    cfg = Config(str(alembic_ini))
    # Ensure the script location points to the repo's alembic package
    cfg.set_main_option("script_location", str(backend_dir / "alembic"))

    try:
        logger.info("Running Alembic upgrade head using config %s", alembic_ini)
        command.upgrade(cfg, "head")
        logger.info("Migrations applied successfully")
        return 0
    except Exception as exc:
        logger.exception("Migration run failed: %s", exc)
        return 1


if __name__ == "__main__":
    sys.exit(main())
