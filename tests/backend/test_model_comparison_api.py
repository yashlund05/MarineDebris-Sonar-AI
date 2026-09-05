import pytest
from httpx import AsyncClient, ASGITransport
from backend.api.main import app

@pytest.mark.asyncio
async def test_models_comparison():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/api/v1/models-comparison")
        assert response.status_code == 200
        res_json = response.json()
        assert res_json["success"] is True
        data = res_json["data"]
        assert "compared_models" in data
        assert len(data["compared_models"]) > 0
        assert "weighting_schema" in data
        assert "rank" in data["compared_models"][0]
