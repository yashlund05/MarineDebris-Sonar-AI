"""Pytest fixtures and configuration for backend tests."""

import os
import pytest
from typing import AsyncGenerator
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# Force test environment variables
os.environ["ENVIRONMENT"] = "test"
os.environ["DEBUG"] = "false"
os.environ["CELERY_TASK_ALWAYS_EAGER"] = "true"
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"

from backend.api.main import create_app
from backend.api.dependencies import get_db
from backend.database.models import Base

test_engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
TestSessionLocal = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


@pytest.fixture(scope="function")
async def async_db() -> AsyncGenerator[AsyncSession, None]:
    """Provide clean database session for each test."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with TestSessionLocal() as session:
        yield session

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture(scope="function")
async def client(async_db: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Provide AsyncClient connected to FastAPI app with overridden DB dependency."""
    app = create_app()

    async def override_get_db():
        yield async_db

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()
