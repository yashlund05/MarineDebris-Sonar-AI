"""Comprehensive regression & acceptance tests for FLS Sonar ML Integration."""

import uuid
import json
from datetime import datetime, timezone
import pytest
import numpy as np
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.ml.detector.yolo_detector import YOLOv8Detector, FLS_TRAINED_CLASSES
from backend.ml.segmentation.unet import UNetSegmenter
from backend.ml.segmentation.segformer import SegFormerSegmenter
from backend.ml.classifier.mobilenet import MobileNetClassifier
from backend.ml.classifier.resnet import ResNetClassifier
from backend.ml.fusion.inference_fusion import InferenceFusion, FusedDetectionResult
from backend.ml.registry.model_registry import ModelRegistryService
from backend.ml.pipeline.inference_pipeline import InferencePipeline
from backend.database.models import Detection, ProcessingJob, Survey
from backend.tasks import _publish_progress


# 1. Detector Model Loading & Missing Weights
def test_yolo_detector_missing_weights_truthful():
    """Verify detector reports MISSING_WEIGHTS when weights file does not exist."""
    detector = YOLOv8Detector(weights_path="models/detection/non_existent_weights.pt")
    health = detector.health()
    assert health.status == "MISSING_WEIGHTS"
    assert not health.is_ready
    assert "Checkpoint file not found" in health.details


def test_yolo_detector_predict_graceful_on_missing_weights():
    """Verify detector returns empty detections without error or fabrication when weights are absent."""
    detector = YOLOv8Detector(weights_path="models/detection/non_existent_weights.pt")
    dummy_tiles = [np.zeros((640, 640, 3), dtype=np.uint8) for _ in range(2)]
    results = detector.predict(dummy_tiles)
    assert len(results) == 2
    assert results[0] == []
    assert results[1] == []


# 2. Segmentation Unavailable & Truthful Output Validation
def test_segmentation_unavailable_truthful():
    """Verify UNet and SegFormer report unavailable when weights are missing."""
    unet = UNetSegmenter(weights_path="models/segmentation/non_existent.pt")
    unet_health = unet.health()
    assert unet_health["status"] == "MISSING_WEIGHTS"
    assert not unet_health["is_ready"]

    seg_res = unet.predict(tile=np.zeros((640, 640), dtype=np.float32), bbox={"x": 10, "y": 10, "width": 50, "height": 50})
    assert seg_res.status == "unavailable"
    assert seg_res.mask_area is None

    segformer = SegFormerSegmenter(weights_path="models/segmentation/non_existent.pt")
    sf_health = segformer.health()
    assert sf_health["status"] == "MISSING_WEIGHTS"


# 3. Classifier Unavailable & Output Validation
def test_classifier_unavailable_truthful():
    """Verify MobileNet and ResNet report unavailable when weights are absent."""
    mobilenet = MobileNetClassifier(weights_path="models/classification/non_existent.pt")
    health = mobilenet.health()
    assert health["status"] == "MISSING_WEIGHTS"
    assert not health["is_ready"]

    res = mobilenet.predict(crop=np.zeros((64, 64, 3), dtype=np.uint8))
    assert res.status == "unavailable"

    resnet = ResNetClassifier(weights_path="models/classification/non_existent.pt")
    assert resnet.health()["status"] == "MISSING_WEIGHTS"


# 4. Model Registry & Supported/Unsupported Classes
def test_model_registry_catalog_and_classes():
    """Verify catalog exposes truthful status, device, and differentiates trained vs untrained classes."""
    catalog = ModelRegistryService.list_catalog()
    assert len(catalog) >= 3

    yolo_entry = next((m for m in catalog if m["architecture"] == "YOLOv8m"), None)
    assert yolo_entry is not None
    assert yolo_entry["supported_classes"] == ["general_marine_debris", "other_man_made_target"]
    assert "derelict_fishing_gear" in yolo_entry["unsupported_classes"]
    assert "shipwreck" in yolo_entry["unsupported_classes"]
    assert "pipe_or_cylinder" in yolo_entry["unsupported_classes"]
    assert yolo_entry["status"] in ("MISSING_WEIGHTS", "READY")


# 5. Detection + Classifier Integration (Decision Fusion)
def test_inference_fusion_agreement():
    """Verify decision fusion handles agreement and disagreement without silent override."""
    from backend.ml.classifier.base import ClassificationResult

    # Case 1: Classifier unavailable
    fused_unavail = InferenceFusion.fuse(
        detector_class="general_marine_debris",
        detector_confidence=0.85,
        classification_result=ClassificationResult.unavailable(),
    )
    assert fused_unavail.classification_status == "unavailable"
    assert fused_unavail.final_class_name == "general_marine_debris"
    assert fused_unavail.classification_agreement is None

    # Case 2: Agreement
    agree_result = ClassificationResult(
        status="available",
        class_name="general_marine_debris",
        confidence=0.92,
    )
    fused_agree = InferenceFusion.fuse(
        detector_class="general_marine_debris",
        detector_confidence=0.85,
        classification_result=agree_result,
        classifier_name="MobileNet",
    )
    assert fused_agree.classification_status == "available"
    assert fused_agree.classification_agreement is True
    assert fused_agree.final_class_name == "general_marine_debris"

    # Case 3: Disagreement without override
    disagree_result = ClassificationResult(
        status="available",
        class_name="other_man_made_target",
        confidence=0.70,
    )
    fused_disagree = InferenceFusion.fuse(
        detector_class="general_marine_debris",
        detector_confidence=0.85,
        classification_result=disagree_result,
        classifier_name="MobileNet",
        allow_override=False,
    )
    assert fused_disagree.classification_agreement is False
    assert fused_disagree.final_class_name == "general_marine_debris"  # Preserved YOLO class


# 6. WebSocket Progress Event Generation
def test_websocket_progress_event_formatting(monkeypatch):
    """Verify websocket event dictionary contains required granular stage and progress info."""
    captured_events = []

    class DummyRedis:
        def publish(self, channel, message):
            captured_events.append((channel, json.loads(message)))

        def close(self):
            pass

    import redis
    monkeypatch.setattr(redis, "from_url", lambda *args, **kwargs: DummyRedis())

    _publish_progress(
        redis_url="redis://localhost:6379/0",
        job_id="11111111-1111-1111-1111-111111111111",
        status="running",
        progress_pct=75,
        current_stage="Segmentation",
        stage_enum="SEGMENTING",
        message="Segmenting detected sonar targets",
    )

    assert len(captured_events) == 1
    channel, event = captured_events[0]
    assert channel == "job_progress:11111111-1111-1111-1111-111111111111"
    assert event["stage"] == "SEGMENTING"
    assert event["progress_pct"] == 75
    assert event["message"] == "Segmenting detected sonar targets"


# 7. Database Persistence for ML Fields
@pytest.mark.asyncio
async def test_database_detection_ml_fields_persistence(async_db: AsyncSession):
    """Verify Detection ORM model stores and retrieves segmentation and classification columns."""
    survey = Survey(
        id=uuid.uuid4(),
        source_filename="test_survey.png",
        storage_path="/tmp/test.png",
        file_type="png",
        file_size_bytes=1024,
        status="uploaded",
    )
    job = ProcessingJob(
        id=uuid.uuid4(),
        survey_id=survey.id,
        status="complete",
        progress_pct=100,
    )
    detection = Detection(
        id=uuid.uuid4(),
        survey_id=survey.id,
        job_id=job.id,
        detection_code="MD-0001",
        class_name="general_marine_debris",
        confidence=0.88,
        bbox_x=50,
        bbox_y=60,
        bbox_w=70,
        bbox_h=80,
        segmentation_status="unavailable",
        classification_status="available",
        classifier_name="MobileNet",
        classifier_class="general_marine_debris",
        classifier_confidence=0.91,
        classification_agreement=True,
    )

    async_db.add(survey)
    async_db.add(job)
    async_db.add(detection)
    await async_db.commit()

    # Query back
    result = await async_db.execute(select(Detection).where(Detection.id == detection.id))
    fetched = result.scalar_one()
    assert fetched.segmentation_status == "unavailable"
    assert fetched.classifier_name == "MobileNet"
    assert fetched.classification_agreement is True


# 8. API Endpoints: Models, Health, Metrics, and Reanalyze
@pytest.mark.asyncio
async def test_api_models_health_and_metrics(client: AsyncClient):
    """Verify /models, /models/{id}/health, and /models/{id}/metrics endpoints."""
    # List models
    resp = await client.get("/api/v1/models")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert len(data) >= 3

    yolo_model = data[0]
    model_id = yolo_model["id"]

    # Get model health
    health_resp = await client.get(f"/api/v1/models/{model_id}/health")
    assert health_resp.status_code == 200
    health_data = health_resp.json()["data"]
    assert "status" in health_data
    assert "supported_classes" in health_data

    # Get model metrics
    metrics_resp = await client.get(f"/api/v1/models/{model_id}/metrics")
    assert metrics_resp.status_code == 200
    metrics_data = metrics_resp.json()["data"]
    assert "metrics" in metrics_data


@pytest.mark.asyncio
async def test_api_surveys_reanalyze_endpoint(client: AsyncClient, async_db: AsyncSession):
    """Verify /surveys/{id}/reanalyze triggers job with configurable ML model flags."""
    survey = Survey(
        id=uuid.uuid4(),
        source_filename="test_fls.png",
        storage_path="/tmp/fls.png",
        file_type="png",
        file_size_bytes=2048,
        status="complete",
    )
    async_db.add(survey)
    await async_db.commit()

    reanalyze_payload = {
        "detection_conf_threshold": 0.40,
        "nms_iou_threshold": 0.50,
        "enable_segmentation": True,
        "enable_classification": False,
        "detector_model": "sonar_yolov8m_ghostpot_v1",
    }

    resp = await client.post(f"/api/v1/surveys/{survey.id}/reanalyze", json=reanalyze_payload)
    assert resp.status_code == 201
    resp_data = resp.json()["data"]
    assert "job_id" in resp_data
    assert resp_data["models_configured"]["detector"] == "sonar_yolov8m_ghostpot_v1"
    assert resp_data["models_configured"]["classification"] == "disabled"
