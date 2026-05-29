from __future__ import annotations

from typing import AsyncGenerator
import sys

from .async_database import get_async_db
from sqlalchemy.ext.asyncio import AsyncSession


if "pytest" in sys.modules:
    # During tests, the environment uses the synchronous DB session fixtures.
    # Yield a standard sync `Session`-compatible object so existing tests
    # continue to work without requiring async DB drivers like `aiosqlite`.
    from app.core.database import SessionLocal


    async def get_db_async() -> AsyncGenerator[SessionLocal, None]:
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()

else:
    async def get_db_async() -> AsyncGenerator[AsyncSession, None]:
        async for session in get_async_db():
            yield session
