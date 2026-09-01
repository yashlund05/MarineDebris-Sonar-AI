"""Complete Backend End-to-End (E2E) Pipeline Integration Test.

Tests the complete 20-step lifecycle:
  Upload Survey -> Validate -> Storage -> Survey DB -> ProcessingJob DB ->
  Ingestion -> Quality Assessment -> Preprocessing -> Tiling ->
  Inference Interface -> Postprocessing (NMS + Filters + Calibration) ->
  Georeferencing (WGS84) -> Detections Persistence -> Reports Generation (JSON, CSV, GeoJSON) ->
  Report Download -> Verification.
"""

import os
import uuid
import pytest
import numpy as np
import cv2
from pathlib import Path
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy import select, create_engine
from sqlalchemy.orm import Session

from backend.api.main import create_app
from backend.api.dependencies import get_db
from backend.database.models import Base, Survey, ProcessingJob, Detection, Report
from backend.tasks import process_survey


TEST_DB_FILE = Path("./data/test_e2e.db")
TEST_ASYNC_URL = f"sqlite+aiosqlite:///{TEST_DB_FILE.as_posix()}"
TEST_SYNC_URL = f"sqlite:///{TEST_DB_FILE.as_posix()}"


@pytest.fixture(scope="module")
def e2e_database():
    """Setup and teardown a file-backed SQLite database for sync/async sharing in E2E test."""
    TEST_DB_FILE.parent.mkdir(parents=True, exist_ok=True)
    if TEST_DB_FILE.exists():
        TEST_DB_FILE.unlink()

    # Set environment variables for the test duration
    old_db_url = os.environ.get("DATABASE_URL")
    os.environ["DATABASE_URL"] = TEST_ASYNC_URL

    from backend.config import get_settings
    get_settings.cache_clear()

    sync_engine = create_engine(TEST_SYNC_URL)
    Base.metadata.create_all(sync_engine)

    yield sync_engine

    Base.metadata.drop_all(sync_engine)
    sync_engine.dispose()
    if TEST_DB_FILE.exists():
        try:
            TEST_DB_FILE.unlink()
        except Exception:
            pass

    if old_db_url:
        os.environ["DATABASE_URL"] = old_db_url
    else:
        os.environ.pop("DATABASE_URL", None)
    get_settings.cache_clear()


@pytest.fixture
def synthetic_sonar_png() -> bytes:
    """Create synthetic sidescan sonar PNG bytes (1000 pings x 640 columns)."""
    img = np.random.uniform(0.1, 0.9, (1000, 640)).astype(np.float32)
    # Add a bright target anomaly and shadow
    img[400:440, 200:250] = 0.95
    img[400:440, 250:320] = 0.05
    img_uint8 = (img * 255).astype(np.uint8)
    success, buffer = cv2.imencode(".png", img_uint8)
    assert success
    return buffer.tobytes()


@pytest.fixture
def synthetic_nav_csv() -> bytes:
    """Create synthetic navigation CSV bytes matching pings."""
    lines = ["ping_number,timestamp,latitude,longitude,heading,altitude,range_m"]
    base_lat = 18.9220
    base_lon = 72.8347
    for ping in range(1000):
        lat = base_lat + (ping * 0.00001)
        lon = base_lon + (ping * 0.000005)
        lines.append(f"{ping},{ping * 0.1:.2f},{lat:.6f},{lon:.6f},45.0,15.0,75.0")
    return "\n".join(lines).encode("utf-8")


@pytest.mark.asyncio
async def test_full_backend_e2e_pipeline(e2e_database, synthetic_sonar_png, synthetic_nav_csv):
    """Execute and verify complete backend E2E pipeline without frontend dependency."""
    async_engine = create_async_engine(TEST_ASYNC_URL, echo=False)
    session_maker = async_sessionmaker(bind=async_engine, class_=AsyncSession, expire_on_commit=False)

    app = create_app()

    async def override_get_db():
        async with session_maker() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Step 1: Health Check verification
        health_resp = await client.get("/api/v1/health")
        assert health_resp.status_code == 200
        health_data = health_resp.json()
        assert "status" in health_data
        assert "device" in health_data

        # Step 2: Upload Survey with auxiliary navigation CSV
        files = {
            "file": ("e2e_survey_starboard.png", synthetic_sonar_png, "image/png"),
            "nav_csv": ("e2e_navigation.csv", synthetic_nav_csv, "text/csv"),
        }
        data = {"channel": "starboard"}

        upload_resp = await client.post("/api/v1/surveys/upload", files=files, data=data)
        assert upload_resp.status_code == 201, upload_resp.text
        upload_data = upload_resp.json()["data"]

        survey_id = upload_data["survey_id"]
        job_id = upload_data["job_id"]
        assert survey_id is not None
        assert job_id is not None
        assert upload_data["source_filename"] == "e2e_survey_starboard.png"

        # Step 3: Verify initial database state in async DB
        async with session_maker() as session:
            survey_res = await session.execute(select(Survey).where(Survey.id == uuid.UUID(survey_id)))
            survey = survey_res.scalar_one_or_none()
            assert survey is not None
            assert survey.status in ("uploaded", "queued", "running")

            job_res = await session.execute(select(ProcessingJob).where(ProcessingJob.id == uuid.UUID(job_id)))
            job = job_res.scalar_one_or_none()
            assert job is not None

        # Step 4: Execute processing task synchronously (in-process eager execution)
        task_result = process_survey(survey_id, job_id)
        assert task_result["status"] == "complete"
        assert task_result["survey_id"] == survey_id
        assert task_result["job_id"] == job_id

        # Step 5: Verify post-processing survey state in DB
        async with session_maker() as session:
            survey_res = await session.execute(select(Survey).where(Survey.id == uuid.UUID(survey_id)))
            survey = survey_res.scalar_one_or_none()
            assert survey.status == "complete"
            assert survey.processing_completed_at is not None

        # Step 6: Verify API query for survey detail
        get_survey_resp = await client.get(f"/api/v1/surveys/{survey_id}")
        assert get_survey_resp.status_code == 200
        survey_detail = get_survey_resp.json()["data"]
        assert survey_detail["id"] == survey_id
        assert survey_detail["status"] == "complete"

        # Step 7: Verify Detections API
        detections_resp = await client.get(f"/api/v1/surveys/{survey_id}/detections?include_filtered=true")
        assert detections_resp.status_code == 200
        detections_envelope = detections_resp.json()
        assert detections_envelope["success"] is True
        assert "data" in detections_envelope
        assert isinstance(detections_envelope["data"], list)

        # Step 8: Generate Reports (JSON, CSV, GeoJSON)
        # 8a: JSON Report
        json_rep_resp = await client.post(
            f"/api/v1/surveys/{survey_id}/reports/generate",
            json={"format": "json"},
        )
        assert json_rep_resp.status_code == 201
        json_report_id = json_rep_resp.json()["data"]["report_id"]

        # 8b: CSV Report
        csv_rep_resp = await client.post(
            f"/api/v1/surveys/{survey_id}/reports/generate",
            json={"format": "csv"},
        )
        assert csv_rep_resp.status_code == 201
        csv_report_id = csv_rep_resp.json()["data"]["report_id"]

        # 8c: GeoJSON Report
        geojson_rep_resp = await client.post(
            f"/api/v1/surveys/{survey_id}/reports/generate",
            json={"format": "geojson"},
        )
        assert geojson_rep_resp.status_code == 201
        geojson_report_id = geojson_rep_resp.json()["data"]["report_id"]

        # Step 9: Verify Reports list API
        reports_list_resp = await client.get(f"/api/v1/surveys/{survey_id}/reports")
        assert reports_list_resp.status_code == 200
        reports_list = reports_list_resp.json()["data"]
        assert len(reports_list) >= 3

        # Step 10: Download and verify report contents
        # Download JSON report
        dl_json_resp = await client.get(f"/api/v1/reports/{json_report_id}/download")
        assert dl_json_resp.status_code == 200
        assert dl_json_resp.headers["content-type"] == "application/json"

        # Download CSV report
        dl_csv_resp = await client.get(f"/api/v1/reports/{csv_report_id}/download")
        assert dl_csv_resp.status_code == 200
        assert "text/csv" in dl_csv_resp.headers["content-type"]

        # Download GeoJSON report
        dl_geojson_resp = await client.get(f"/api/v1/reports/{geojson_report_id}/download")
        assert dl_geojson_resp.status_code == 200
        assert dl_geojson_resp.headers["content-type"] == "application/geo+json"

        # Step 11: Reprocess Survey endpoint
        reprocess_resp = await client.post(
            f"/api/v1/surveys/{survey_id}/reprocess",
            json={"detection_conf_threshold": 0.40, "nms_iou_threshold": 0.50},
        )
        assert reprocess_resp.status_code == 201
        new_job_id = reprocess_resp.json()["data"]["job_id"]
        assert new_job_id != job_id

        # Step 12: Delete Survey cascade verification
        delete_resp = await client.delete(f"/api/v1/surveys/{survey_id}")
        assert delete_resp.status_code == 200
        assert delete_resp.json()["data"]["deleted"] is True

        # Verify Survey is gone
        get_deleted_resp = await client.get(f"/api/v1/surveys/{survey_id}")
        assert get_deleted_resp.status_code == 404

    await async_engine.dispose()
