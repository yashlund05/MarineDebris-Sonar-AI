"""
API Integration Tests for SidescanTools Sonar Enhancement Endpoints.
Smart India Hackathon 2026 — PS26057.
"""

import io
import pytest
import numpy as np
import cv2
from httpx import AsyncClient, ASGITransport
from backend.api.main import app


@pytest.fixture
def synthetic_png_file():
    arr = np.random.randint(30, 220, (128, 128), dtype=np.uint8)
    _, buf = cv2.imencode(".png", arr)
    return io.BytesIO(buf.tobytes())


@pytest.mark.asyncio
async def test_get_palettes():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.get("/api/v1/sonar/palettes")
        assert res.status_code == 200
        data = res.json()
        assert data["success"] is True
        assert len(data["palettes"]) >= 5
        palette_ids = [p["id"] for p in data["palettes"]]
        assert "amber" in palette_ids
        assert "viridis" in palette_ids
        assert "grayscale" in palette_ids


@pytest.mark.asyncio
async def test_get_samples():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.get("/api/v1/sonar/samples?dataset_version=v3&split=val&limit=5")
        assert res.status_code == 200
        data = res.json()
        assert data["success"] is True
        assert "samples" in data


@pytest.mark.asyncio
async def test_enhance_image_smoke_default():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        payload = {
            "colormap": "amber",
            "stripe_noise_filter": True,
            "clahe": True,
        }
        res = await client.post("/api/v1/sonar/enhance", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert data["success"] is True
        assert "raw_image_data_url" in data
        assert "enhanced_grayscale_data_url" in data
        assert "pseudocolor_data_url" in data
        assert "metrics" in data
        assert "audit_trail" in data
        assert "raw_sha256" in data


@pytest.mark.asyncio
async def test_enhance_upload_multipart(synthetic_png_file):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        files = {"file": ("test_sonar.png", synthetic_png_file, "image/png")}
        data = {"colormap": "inferno", "clahe_clip_limit": "0.02"}
        res = await client.post("/api/v1/sonar/enhance/upload", files=files, data=data)
        assert res.status_code == 200
        res_data = res.json()
        assert res_data["success"] is True
        assert res_data["colormap"] == "inferno"
        assert res_data["metrics"]["raw"]["rms_contrast"] >= 0.0


@pytest.mark.asyncio
async def test_recolor_cached_frame():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # First enhance
        payload = {"colormap": "amber"}
        enh_res = await client.post("/api/v1/sonar/enhance", json=payload)
        assert enh_res.status_code == 200
        cache_key = enh_res.json()["cache_key"]

        # Fast recolor
        recolor_res = await client.post(
            "/api/v1/sonar/recolor",
            json={"cache_key": cache_key, "colormap": "magma"},
        )
        assert recolor_res.status_code == 200
        data = recolor_res.json()
        assert data["success"] is True
        assert data["colormap"] == "magma"
        assert "pseudocolor_data_url" in data


@pytest.mark.asyncio
async def test_download_image():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # First enhance
        enh_res = await client.post("/api/v1/sonar/enhance", json={"colormap": "amber"})
        cache_key = enh_res.json()["cache_key"]

        # Download raw
        dl_res = await client.get(f"/api/v1/sonar/download?cache_key={cache_key}&target=raw")
        assert dl_res.status_code == 200
        assert dl_res.headers["content-type"] == "image/png"
        assert len(dl_res.content) > 100
