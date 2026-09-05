import pytest
from httpx import AsyncClient, ASGITransport
from backend.api.main import app

@pytest.mark.asyncio
async def test_promotion_audit():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/api/v1/models-promotion/audit")
        assert response.status_code == 200
        res_json = response.json()
        assert res_json["success"] is True
        data = res_json["data"]
        assert data["current_production_model_id"] == "production_fls_yolov8n"
        assert data["current_production_sha256"] == "e1215c7e7f6e4f3722398bf93d975eb5013c49f78355d0d5f54ce982d495b3d7"
        assert data["promotion_policy"] == "STRICT_HUMAN_IN_THE_LOOP_OPT_IN"
        assert len(data["audit_records"]) > 0
