import logging
import json
import uuid
import time
from datetime import datetime, timezone
from typing import Any, Dict

from backend.celery_app import celery_app
from backend.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

def _publish_progress(redis_url: str, job_id: str, status: str, progress_pct: int, current_stage: str):
    import redis
    try:
        r = redis.from_url(redis_url)
        event = {
            "event": "job_progress" if status not in ("complete", "failed") else f"job_{status}",
            "job_id": job_id,
            "status": status,
            "progress_pct": progress_pct,
            "current_stage": current_stage,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        r.publish(f"job_progress:{job_id}", json.dumps(event))
        r.close()
    except Exception as e:
        logger.warning(f"Failed to publish progress for job {job_id}: {e}")

def _update_job_progress(job_id: str, status: str, progress_pct: int, current_stage: str, error_message: str = None, survey_id: str = None):
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
                "updated_at": datetime.now(timezone.utc)
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
    
    def update_state(pct: int, stage: str, status: str = "running"):
        _update_job_progress(job_id, status, pct, stage, survey_id=survey_id)
        _publish_progress(redis_url, job_id, status, pct, stage)
        
    try:
        update_state(0, "Starting")
        time.sleep(0.5) # Simulated delay
        
        update_state(5, "Ingestion")
        time.sleep(0.5)
        
        update_state(15, "Quality assessment")
        time.sleep(0.5)
        
        update_state(30, "Preprocessing")
        time.sleep(0.5)
        
        update_state(45, "Tiling")
        time.sleep(0.5)
        
        update_state(60, "Detection")
        time.sleep(0.5)
        
        update_state(70, "Segmentation")
        time.sleep(0.5)
        
        update_state(80, "Post-processing")
        time.sleep(0.5)
        
        update_state(85, "Georeferencing")
        time.sleep(0.5)
        
        update_state(90, "Persisting detections")
        time.sleep(0.5)
        
        update_state(95, "Generating reports")
        time.sleep(0.5)
        
        update_state(100, "Complete", status="complete")
        
        return {"status": "complete", "job_id": job_id, "survey_id": survey_id}
        
    except Exception as e:
        logger.exception(f"Error processing survey {survey_id}")
        error_msg = str(e)
        _update_job_progress(job_id, "failed", 0, "Failed", error_message=error_msg, survey_id=survey_id)
        _publish_progress(redis_url, job_id, "failed", 0, "Failed")
        raise
