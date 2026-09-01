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

from functools import lru_cache

@lru_cache(maxsize=4)
def _get_cached_async_engine(url: str, debug: bool) -> AsyncEngine:
    kwargs = {"echo": debug, "future": True}
    if "sqlite" in url:
        kwargs["connect_args"] = {"check_same_thread": False}
    else:
        kwargs["pool_pre_ping"] = True
    return create_async_engine(url, **kwargs)


@lru_cache(maxsize=4)
def _get_cached_sync_engine(url: str, debug: bool) -> Engine:
    kwargs = {"echo": debug}
    if "sqlite" in url:
        kwargs["connect_args"] = {"check_same_thread": False}
    else:
        kwargs["pool_pre_ping"] = True
    return create_engine(url, **kwargs)


def get_async_engine() -> AsyncEngine:
    """Return active async database engine."""
    current_settings = get_settings()
    return _get_cached_async_engine(current_settings.async_database_url, current_settings.DEBUG)


def get_sync_engine() -> Engine:
    """Return synchronous database engine for migrations or background workers."""
    current_settings = get_settings()
    return _get_cached_sync_engine(current_settings.sync_database_url, current_settings.DEBUG)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for injecting async database session into FastAPI routes."""
    engine = get_async_engine()
    session_factory = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )
    async with session_factory() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
