import pytest
from backend.config import get_settings

settings = get_settings()
api_prefix = settings.API_V1_STR


@pytest.mark.asyncio
async def test_list_models(client):
    response = await client.get(f"{api_prefix}/models")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert isinstance(data["data"], list)
    model_ids = [m["id"] for m in data["data"]]
    # Should include production and experiment models
    assert "production_fls_yolov8n" in model_ids
    assert any("E6" in mid or "P3_" in mid for mid in model_ids)


@pytest.mark.asyncio
async def test_get_model_production(client):
    response = await client.get(f"{api_prefix}/models/production_fls_yolov8n")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["model_id"] == "production_fls_yolov8n"
    assert data["data"]["is_production"] is True
    assert data["data"]["checkpoint_sha256"] == "e1215c7e7f6e4f3722398bf93d975eb5013c49f78355d0d5f54ce982d495b3d7"


@pytest.mark.asyncio
async def test_get_model_metrics(client):
    # Test production metrics
    response = await client.get(f"{api_prefix}/models/production_fls_yolov8n/metrics")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["confidence"] == "VERIFIED"
    assert "canonical_v3" in data["data"]
    assert data["data"]["canonical_v3"]["mAP50"] == 0.9192

    # Test candidate E6 metrics
    res_e6 = await client.get(f"{api_prefix}/models/P3_E6_SEED_2026/metrics")
    assert res_e6.status_code == 200
    d_e6 = res_e6.json()["data"]
    assert d_e6["confidence"] == "VERIFIED"
    assert d_e6["v3_test"]["mAP50"] == 0.9742


@pytest.mark.asyncio
async def test_get_model_runs_multiseed(client):
    response = await client.get(f"{api_prefix}/models/P3_E6_SEED_2026/runs")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    ms = data["data"]["multiseed"]
    assert ms["confidence"] == "VERIFIED"
    assert ms["seeds_trained"] == [42, 123, 2026]
    assert ms["best_seed"] == 2026
    assert ms["statistical_distribution"]["v3_mAP50"]["mean"] == 0.9594
    assert ms["statistical_distribution"]["v3_mAP50"]["std"] == 0.0105


@pytest.mark.asyncio
async def test_get_model_artifacts(client):
    response = await client.get(f"{api_prefix}/models/production_fls_yolov8n/artifacts")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["confidence"] == "VERIFIED"
    assert len(data["data"]["artifacts"]) > 0


@pytest.mark.asyncio
async def test_get_model_promotion_and_explanations(client):
    # E6 promotion decision
    res = await client.get(f"{api_prefix}/models/P3_E6_SEED_2026/promotion")
    assert res.status_code == 200
    d = res.json()["data"]
    assert d["confidence"] == "VERIFIED"
    assert d["promotion_gate"]["status"] == "REJECTED"
    assert "195.13 ms" in d["rationale"]

    # Explanations
    res_exp = await client.get(f"{api_prefix}/models/P3_E6_SEED_2026/explanations")
    assert res_exp.status_code == 200
    exp_d = res_exp.json()["data"]
    assert len(exp_d["strengths"]) > 0
    assert len(exp_d["weaknesses"]) > 0


@pytest.mark.asyncio
async def test_missing_model_handled_gracefully(client):
    response = await client.get(f"{api_prefix}/models/non_existent_model_id_123")
    assert response.status_code == 404

    # Metrics for missing model returns NOT_AVAILABLE or 404
    res_m = await client.get(f"{api_prefix}/models/non_existent_model_id_123/metrics")
    assert res_m.status_code in (200, 404)
    if res_m.status_code == 200:
        assert res_m.json()["data"]["confidence"] == "NOT_AVAILABLE"
