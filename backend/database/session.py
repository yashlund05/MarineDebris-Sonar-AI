"""Database session and engine management using SQLAlchemy 2.0 async."""

from typing import AsyncGenerator
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from backend.config import get_settings

settings = get_settings()

# Async Engine for FastAPI route handlers
async_engine: AsyncEngine = create_async_engine(
    settings.async_database_url,
    echo=settings.DEBUG,
    future=True,
    pool_pre_ping=True,
)

# Async Session Factory
AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for injecting async database session into FastAPI routes."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


def get_sync_engine() -> Engine:
    """Return synchronous database engine for migrations or background workers."""
    return create_engine(
        settings.sync_database_url,
        echo=settings.DEBUG,
        pool_pre_ping=True,
    )
