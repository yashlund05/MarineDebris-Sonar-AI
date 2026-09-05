import pytest
from backend.config import get_settings

settings = get_settings()
api_prefix = settings.API_V1_STR

@pytest.mark.asyncio
async def test_list_datasets(client):
    response = await client.get(f"{api_prefix}/datasets")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "versions" in data["data"]

@pytest.mark.asyncio
async def test_get_dataset_detail_v3(client):
    response = await client.get(f"{api_prefix}/datasets/v3")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "manifest" in data["data"]

@pytest.mark.asyncio
async def test_get_dataset_summary_v3(client):
    response = await client.get(f"{api_prefix}/datasets/v3/summary")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    
    summary = data["data"]
    # Check sections and confidence fields
    sections = [
        "overview", "source_level_accounting", "splits",
        "class_distribution", "scale_distribution", "sensor",
        "taxonomy", "provenance", "integrity", "hard_negatives",
        "benchmarks", "variants", "lineage", "limitations"
    ]
    
    for section in sections:
        assert section in summary, f"Missing section {section}"
        
        # Depending on if it's a dict or list, we might have confidence in different places.
        if isinstance(summary[section], dict):
            assert "confidence" in summary[section], f"Missing confidence in {section}"
        elif isinstance(summary[section], list):
            for item in summary[section]:
                if isinstance(item, dict):
                    assert "confidence" in item, f"Missing confidence in list item of {section}"

@pytest.mark.asyncio
async def test_get_dataset_manifest_v3(client):
    response = await client.get(f"{api_prefix}/datasets/v3/manifest")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True

@pytest.mark.asyncio
async def test_dataset_not_found_handled_gracefully(client):
    response = await client.get(f"{api_prefix}/datasets/non_existent_dataset/summary")
    
    # Should still return 200 with NOT_AVAILABLE / defaults instead of crashing
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["overview"]["confidence"] == "NOT_AVAILABLE"

