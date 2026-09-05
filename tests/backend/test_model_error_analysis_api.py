import pytest
from httpx import AsyncClient, ASGITransport
from backend.api.main import app

@pytest.mark.asyncio
async def test_model_error_analysis_production():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/api/v1/models/production_fls_yolov8n/error-analysis")
        assert response.status_code == 200
        res_json = response.json()
        assert res_json["success"] is True
        data = res_json["data"]
        assert data["model_id"] == "production_fls_yolov8n"
        assert "subgroups" in data
        assert "small_lt_40px" in data["subgroups"]
        assert "false_alarm_profile" in data
        assert len(data["error_breakdown_notes"]) > 0

@pytest.mark.asyncio
async def test_model_error_analysis_candidate():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/api/v1/models/P3_E2_NAIVE_MIX/error-analysis")
        assert response.status_code == 200
        res_json = response.json()
        assert res_json["success"] is True
        assert res_json["data"]["model_id"] == "P3_E2_NAIVE_MIX"
