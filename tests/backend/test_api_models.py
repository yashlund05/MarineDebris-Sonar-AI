"""Tests for Model Registry API and ModelLoader truthful state reporting."""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.models import ModelRegistry
from backend.inference.model_loader import ModelLoader


def test_model_loader_missing_weights_truthful():
    """Verify ModelLoader reports MISSING_WEIGHTS when checkpoint does not exist."""
    status = ModelLoader.get_model_status("models/detection/non_existent_weights.pt")
    assert status["state"] == "MISSING_WEIGHTS"
    assert status["is_loaded"] is False
    assert status["device"] in ("cpu", "cuda")


@pytest.mark.asyncio
async def test_api_list_models_with_runtime_status(client: AsyncClient, async_db: AsyncSession):
    """Verify GET /api/v1/models reports model with truthful runtime weight state."""
    # Register a test model with non-existent weights to verify MISSING_WEIGHTS reporting
    model = ModelRegistry(
        model_name="test_missing_model_v1",
        version="1.0.0",
        task="detection",
        architecture="yolov8m",
        training_dataset="ghost_pot_sss",
        weight_path="models/detection/non_existent_weights_check.pt",
        map50=0.724,
        is_active=False,
    )
    async_db.add(model)
    await async_db.commit()

    response = await client.get("/api/v1/models")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert len(data["data"]) >= 1

    registered = next((m for m in data["data"] if m["model_name"] == "test_missing_model_v1"), None)
    assert registered is not None
    # Since weights do not physically exist on disk, runtime_status must be MISSING_WEIGHTS
    assert registered["runtime_status"] == "MISSING_WEIGHTS"
    assert registered["is_loaded"] is False
    assert registered["is_active"] is False  # Cannot be active without weights
