import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_get_detections_empty(client: AsyncClient):
    """Since survey doesn't exist, it should return 404 (SurveyNotFoundError)."""
    invalid_uuid = "00000000-0000-0000-0000-000000000000"
    response = await client.get(f"/api/v1/surveys/{invalid_uuid}/detections")

    assert response.status_code == 404
    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == "NOT_FOUND"


@pytest.mark.asyncio
async def test_get_detection_not_found(client: AsyncClient):
    """Test getting a non-existent detection returns 404."""
    invalid_uuid = "00000000-0000-0000-0000-000000000000"
    response = await client.get(f"/api/v1/detections/{invalid_uuid}")

    assert response.status_code == 404
    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == "NOT_FOUND"
