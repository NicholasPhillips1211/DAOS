import os
from pathlib import Path

from alembic.config import Config
from alembic import command


def test_alembic_upgrade_head(tmp_path, monkeypatch):
    """Run Alembic migrations against a temporary SQLite DB to ensure
    `alembic upgrade head` completes without error.

    Notes:
    - Some modules (tests' conftest or imports) may instantiate the
      Settings object before this test runs. To ensure Alembic's `env.py`
      uses our temporary DB, update the live `settings.database_url`.
    """
    db_file = tmp_path / "alembic_test.db"
    db_url = f"sqlite:///{db_file}"

    # Also set env var for any code reading env directly
    monkeypatch.setenv("DATABASE_URL", db_url)

    # Ensure the already-instantiated settings object is updated
    try:
        import app.core.config as app_config

        monkeypatch.setattr(app_config.settings, "database_url", db_url, raising=False)
    except Exception:
        # If import fails for any reason, proceed — alembic config override below
        pass

    # Point Alembic at the repo's alembic.ini (backend/alembic.ini)
    repo_root = Path(__file__).resolve().parents[1]
    alembic_ini = repo_root / "alembic.ini"
    cfg = Config(str(alembic_ini))

    # Run migrations to head; will raise on failure
    command.upgrade(cfg, "head")

    # After running migrations a SQLite file should exist
    assert db_file.exists()
