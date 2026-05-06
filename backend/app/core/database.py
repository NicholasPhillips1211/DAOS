from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.core.config import settings


engine = create_engine(settings.database_url, future=True)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False, future=True)


class Base(DeclarativeBase):
    """Shared SQLAlchemy declarative base for all ORM models.

    Using one base lets the startup hook create the full schema in one pass and
    keeps model metadata registration consistent across modules.
    """

    pass
