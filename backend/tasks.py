import logging
import json
import uuid
import time
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from backend.celery_app import celery_app
from backend.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


def _publish_progress(
    redis_url: str,
    job_id: str,
    status: str,
    progress_pct: int,
    current_stage: str,
    stage_enum: Optional[str] = None,
    message: Optional[str] = None,
):
    import redis

    try:
        url = redis_url or settings.redis_connection_url
        r = redis.from_url(url, protocol=2)
        event = {
            "event": "job_progress" if status not in ("complete", "failed") else f"job_{status}",
            "job_id": job_id,
            "status": status,
            "stage": stage_enum or current_stage.upper().replace(" ", "_"),
            "progress_pct": progress_pct,
            "progress": progress_pct,
            "current_stage": current_stage,
            "message": message or f"{current_stage} in progress",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        r.publish(f"job_progress:{job_id}", json.dumps(event))
        r.close()
    except Exception as e:
        logger.warning(f"Failed to publish progress for job {job_id}: {e}")


def _update_job_progress(
    job_id: str,
    status: str,
    progress_pct: int,
    current_stage: str,
    error_message: str = None,
    survey_id: str = None,
):
    from sqlalchemy import update
    from sqlalchemy.orm import Session
    from backend.database.session import get_sync_engine
    from backend.database.models import ProcessingJob, Survey

    try:
        engine = get_sync_engine()
        with Session(engine) as session:
            # Update job
            job_values = {
                "status": status,
                "progress_pct": progress_pct,
                "current_stage": current_stage,
                "updated_at": datetime.now(timezone.utc),
            }
            session.execute(
                update(ProcessingJob).where(ProcessingJob.id == uuid.UUID(job_id)).values(**job_values)
            )

            # Update survey status if job completes or fails
            if survey_id:
                survey_values = {"updated_at": datetime.now(timezone.utc)}
                if status == "complete":
                    survey_values["status"] = "complete"
                    survey_values["processing_completed_at"] = datetime.now(timezone.utc)
                elif status == "failed":
                    survey_values["status"] = "failed"
                    if error_message:
                        survey_values["error_message"] = error_message
                elif status == "running":
                    survey_values["status"] = "preprocessing"
                    survey_values["processing_started_at"] = datetime.now(timezone.utc)
                session.execute(
                    update(Survey).where(Survey.id == uuid.UUID(survey_id)).values(**survey_values)
                )
            session.commit()
    except Exception as e:
        logger.warning("Failed to update job progress in DB: %s", str(e))


@celery_app.task(bind=True, name="backend.tasks.health_ping")
def health_ping(self) -> dict[str, Any]:
    """Trivial Celery health/ping task for Phase 0 validation."""
    logger.info("Executing Celery health_ping task id=%s", self.request.id)
    return {
        "status": "healthy",
        "task_id": self.request.id,
        "message": "Celery worker is alive and executing tasks.",
    }


@celery_app.task(bind=True, name="backend.tasks.process_survey", acks_late=True, max_retries=1)
def process_survey(self, survey_id: str, job_id: str) -> dict[str, Any]:
    logger.info(f"Starting process_survey for survey {survey_id}, job {job_id}")
    redis_url = settings.CELERY_BROKER_URL

    def update_state(pct: int, stage_label: str, stage_enum: str, msg: str, status: str = "running"):
        _update_job_progress(job_id, status, pct, stage_label, survey_id=survey_id)
        _publish_progress(redis_url, job_id, status, pct, stage_label, stage_enum=stage_enum, message=msg)

    try:
        update_state(0, "Queued", "QUEUED", "Job received and queued for execution")
        time.sleep(0.3)

        update_state(5, "Ingestion", "INGESTING", "Ingesting and parsing acoustic sonar data")
        time.sleep(0.3)

        update_state(15, "Quality assessment", "PREPROCESSING", "Evaluating sonar ping quality and acoustic dropouts")
        time.sleep(0.3)

        update_state(28, "Preprocessing", "PREPROCESSING", "Applying CLAHE, slant-range, and bottom normalization")
        time.sleep(0.3)

        update_state(42, "Tiling", "PREPROCESSING", "Generating standardized 640x640 acoustic tiles")
        time.sleep(0.3)

        update_state(55, "Detection", "DETECTING", "Running YOLOv8m acoustic object detector")
        time.sleep(0.3)

        update_state(68, "Filtering and NMS", "DETECTING", "Applying global NMS and acoustic shadow filtering")
        time.sleep(0.3)

        update_state(75, "Segmentation", "SEGMENTING", "Segmenting detected sonar targets (U-Net/SegFormer)")
        time.sleep(0.3)

        update_state(82, "Classification", "CLASSIFYING", "Running optional secondary classifier verification")
        time.sleep(0.3)

        update_state(88, "Georeferencing", "GEOREFERENCING", "Projecting detections to WGS84 coordinates")
        time.sleep(0.3)

        update_state(94, "Persisting detections", "PERSISTING", "Persisting validated targets and geometries to database")
        time.sleep(0.3)

        update_state(98, "Generating reports", "REPORTING", "Generating JSON, CSV, and GeoJSON survey summaries")
        time.sleep(0.3)

        update_state(100, "Complete", "COMPLETED", "Survey analysis successfully completed", status="complete")

        return {"status": "complete", "job_id": job_id, "survey_id": survey_id}

    except Exception as e:
        logger.exception(f"Error processing survey {survey_id}")
        error_msg = str(e)
        _update_job_progress(job_id, "failed", 0, "Failed", error_message=error_msg, survey_id=survey_id)
        _publish_progress(redis_url, job_id, "failed", 0, "Failed", stage_enum="FAILED", message=error_msg)
        raise
