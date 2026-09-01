import asyncio
import json
import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Path
import redis.asyncio as aioredis
from backend.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

router = APIRouter(prefix="/ws", tags=["WebSockets"])

@router.websocket("/jobs/{job_id}")
async def job_progress_ws(
    websocket: WebSocket,
    job_id: str = Path(..., description="The ID of the processing job")
):
    """WebSocket endpoint for streaming job progress events."""
    await websocket.accept()
    
    redis = None
    pubsub = None
    try:
        redis = aioredis.from_url(settings.celery_broker, protocol=2)
        pubsub = redis.pubsub()
        channel = f"job_progress:{job_id}"
        await pubsub.subscribe(channel)
        
        logger.info(f"WebSocket connected and subscribed to {channel}")
        
        # We need a task to read from pubsub and send to websocket
        async for message in pubsub.listen():
            if message["type"] == "message":
                data = message["data"]
                # decode bytes to string if needed
                if isinstance(data, bytes):
                    data = data.decode('utf-8')
                await websocket.send_text(data)
                
                # Check if job is complete or failed to close connection optionally
                try:
                    event_data = json.loads(data)
                    if event_data.get("status") in ("complete", "failed"):
                        # We could close here or let the client close
                        pass
                except json.JSONDecodeError:
                    pass

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for job {job_id}")
    except Exception as e:
        logger.error(f"WebSocket error for job {job_id}: {e}")
        try:
            await websocket.close(code=1011, reason="Internal error")
        except Exception:
            pass
    finally:
        if pubsub:
            await pubsub.unsubscribe(f"job_progress:{job_id}")
            await pubsub.close()
        if redis:
            await redis.close()
