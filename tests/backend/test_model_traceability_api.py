import pytest
from httpx import AsyncClient, ASGITransport
from backend.api.main import app

@pytest.mark.asyncio
async def test_model_traceability_production():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/api/v1/models/production_fls_yolov8n/traceability")
        assert response.status_code == 200
        res_json = response.json()
        assert res_json["success"] is True
        data = res_json["data"]
        assert data["model_id"] == "production_fls_yolov8n"
        assert data["dataset_version"] in ("v2", "v3")
        assert "lineage_graph" in data
        assert len(data["lineage_graph"]) == 4

@pytest.mark.asyncio
async def test_model_traceability_candidate():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/api/v1/models/P3_E2_NAIVE_MIX/traceability")
        assert response.status_code == 200
        res_json = response.json()
        assert res_json["success"] is True
        data = res_json["data"]
        assert data["model_id"] == "P3_E2_NAIVE_MIX"
        assert data["dataset_version"] == "v3"
