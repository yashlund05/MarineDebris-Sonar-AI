import io
import pytest
import numpy as np
import cv2
from httpx import AsyncClient, ASGITransport
from backend.api.main import app

@pytest.mark.asyncio
async def test_inference_predict_production_checkpoint():
    # Generate dummy sonar frame
    dummy_img = np.random.randint(30, 150, (640, 640, 3), dtype=np.uint8)
    _, encoded = cv2.imencode(".png", dummy_img)
    image_bytes = encoded.tobytes()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        files = {"file": ("test_sonar.png", io.BytesIO(image_bytes), "image/png")}
        data = {
            "model_id": "production_fls_yolov8n",
            "confidence_threshold": "0.25",
            "iou_threshold": "0.45",
        }
        response = await ac.post("/api/v1/inference/predict", files=files, data=data)
        assert response.status_code == 200
        res_json = response.json()
        assert res_json["success"] is True
        resp_data = res_json["data"]
        assert resp_data["model_id"] == "production_fls_yolov8n"
        assert resp_data["is_production_checkpoint"] is True
        assert resp_data["checkpoint_sha256"] == "e1215c7e7f6e4f3722398bf93d975eb5013c49f78355d0d5f54ce982d495b3d7"
        assert "detections" in resp_data
        assert "inference_time_ms" in resp_data
        assert resp_data["total_time_ms"] > 0

@pytest.mark.asyncio
async def test_inference_predict_candidate_model():
    dummy_img = np.random.randint(30, 150, (640, 640, 3), dtype=np.uint8)
    _, encoded = cv2.imencode(".png", dummy_img)
    image_bytes = encoded.tobytes()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        files = {"file": ("test_sonar.png", io.BytesIO(image_bytes), "image/png")}
        data = {
            "model_id": "P3_E2_NAIVE_MIX",
            "confidence_threshold": "0.25",
            "iou_threshold": "0.45",
        }
        response = await ac.post("/api/v1/inference/predict", files=files, data=data)
        assert response.status_code == 200
        res_json = response.json()
        assert res_json["success"] is True
        assert res_json["data"]["model_id"] == "P3_E2_NAIVE_MIX"

@pytest.mark.asyncio
async def test_inference_predict_invalid_image():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        files = {"file": ("corrupt.txt", io.BytesIO(b"not an image"), "text/plain")}
        response = await ac.post("/api/v1/inference/predict", files=files)
        assert response.status_code == 400
