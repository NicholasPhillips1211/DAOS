from __future__ import annotations

from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

from .config import settings


def _to_async_url(sync_url: str) -> str:
    # Convert common sync DB URLs to async variants when possible.
    if "+" in sync_url.split(":", 1)[-1]:
        return sync_url
    if sync_url.startswith("sqlite:///"):
        return sync_url.replace("sqlite://", "sqlite+aiosqlite://", 1)
    if sync_url.startswith("postgresql://"):
        return sync_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    return sync_url


async_engine: AsyncEngine | None = None
async_session: async_sessionmaker[AsyncSession] | None = None


def get_async_engine() -> AsyncEngine:
    global async_engine
    if async_engine is None:
        async_url = _to_async_url(settings.database_url)
        async_engine = create_async_engine(async_url, future=True)
    return async_engine


def get_async_sessionmaker() -> async_sessionmaker[AsyncSession]:
    global async_session
    if async_session is None:
        engine = get_async_engine()
        async_session = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    return async_session


async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    Session = get_async_sessionmaker()
    async with Session() as session:
        yield session
