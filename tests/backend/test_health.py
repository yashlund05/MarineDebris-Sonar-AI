"""Tests for system health endpoints conforming to API_SPEC.md §10."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_root_health(client: AsyncClient):
    """Verify GET /health returns simple healthy status."""
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "MarineDebris-Sonar-AI" in data["service"]


@pytest.mark.asyncio
async def test_api_v1_health(client: AsyncClient):
    """Verify GET /api/v1/health returns system component statuses."""
    response = await client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "database" in data
    assert "redis" in data
    assert "worker" in data
    assert "active_detection_model" in data
    assert "device" in data
    assert data["device"] in ["cpu", "cuda"]
