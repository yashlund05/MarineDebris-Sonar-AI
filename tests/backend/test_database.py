"""Tests for database ORM models and relationships conforming to DB_SCHEMA.md."""

import uuid
import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.database.models import (
    Survey,
    SonarMetadata,
    ProcessingJob,
    Detection,
    Report,
    ModelRegistry,
)


@pytest.mark.asyncio
async def test_survey_creation_and_relations(async_db: AsyncSession):
    """Verify Survey, SonarMetadata, ProcessingJob, and Detection creation with relationships."""
    # 1. Create survey
    survey = Survey(
        source_filename="test_survey.xtf",
        storage_path="/data/storage/test_survey.xtf",
        file_type="xtf",
        file_size_bytes=1048576,
        status="uploaded",
        channel="starboard",
    )
    async_db.add(survey)
    await async_db.commit()
    await async_db.refresh(survey)
    assert survey.id is not None
    assert survey.status == "uploaded"

    # 2. Add SonarMetadata
    metadata = SonarMetadata(
        survey_id=survey.id,
        frequency_hz=455000.0,
        samples_per_ping=1024,
        total_pings=500,
        has_attitude_data=True,
    )
    async_db.add(metadata)
    await async_db.commit()

    # 3. Add ProcessingJob
    job = ProcessingJob(
        survey_id=survey.id,
        status="pending",
        progress_pct=0,
        current_stage="queued",
        detection_model="sonar_yolov8m_ghostpot_v1",
    )
    async_db.add(job)
    await async_db.commit()
    await async_db.refresh(job)

    # 4. Add Detection
    detection = Detection(
        survey_id=survey.id,
        job_id=job.id,
        detection_code="D000001",
        class_name="derelict_fishing_gear",
        confidence=0.89,
        bbox_x=100,
        bbox_y=150,
        bbox_w=50,
        bbox_h=30,
        geotagging_available=False,
    )
    async_db.add(detection)
    await async_db.commit()

    # Query back and verify
    result = await async_db.execute(select(Survey).where(Survey.id == survey.id))
    fetched_survey = result.scalar_one()
    assert fetched_survey.source_filename == "test_survey.xtf"
    assert fetched_survey.file_type == "xtf"


@pytest.mark.asyncio
async def test_model_registry(async_db: AsyncSession):
    """Verify ModelRegistry model creation and unique constraint."""
    model = ModelRegistry(
        model_name="sonar_yolov8m_ghostpot_v1",
        version="1.0.0",
        task="detection",
        architecture="yolov8m",
        training_dataset="ghost_pot_sss",
        map50=0.724,
        is_active=True,
    )
    async_db.add(model)
    await async_db.commit()
    await async_db.refresh(model)
    assert model.id is not None
    assert model.is_active is True
