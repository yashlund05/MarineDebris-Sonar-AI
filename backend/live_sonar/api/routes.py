"""FastAPI REST routes for Live Sonar Subsystem.

Conforms to Requirement R3 of ORIGINAL_REQUEST.md.
"""

from __future__ import annotations

import uuid
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Path, Query, status

from backend.live_sonar.api.schemas import (
    CreateLiveSessionRequest,
    LiveHealthResponse,
    SessionResponse,
)
from backend.live_sonar.models import (
    DropPolicy,
    LiveSonarException,
    LiveSonarSessionConfig,
)
from backend.live_sonar.recording.evidence import capture_evidence
from backend.live_sonar.service import LiveSonarService

router = APIRouter(prefix="/live-sonar", tags=["Live Sonar"])


def get_service() -> LiveSonarService:
    return LiveSonarService.get_instance()


@router.post("/sessions", response_model=Dict[str, Any], status_code=status.HTTP_201_CREATED)
async def create_session(
    req: CreateLiveSessionRequest,
    service: LiveSonarService = Depends(get_service),
):
    """Create a new live sonar streaming session."""
    session_id = req.session_id or f"session_{uuid.uuid4().hex[:12]}"
    try:
        policy = DropPolicy(req.drop_policy.upper())
    except ValueError:
        policy = DropPolicy.DROP_OLDEST

    config = LiveSonarSessionConfig(
        session_id=session_id,
        name=req.name,
        source_type=req.source_type,
        source_uri=req.source_uri,
        target_fps=req.target_fps,
        inference_fps=req.inference_fps,
        buffer_size=req.buffer_size,
        drop_policy=policy,
        preprocessing_profile=req.preprocessing_profile,
        enable_tracking=req.enable_tracking,
        enable_recording=req.enable_recording,
        confidence_threshold=req.confidence_threshold,
        minimum_confirmed_frames=req.minimum_confirmed_frames,
    )

    try:
        res = await service.create_session(config)
        return res
    except LiveSonarException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions", response_model=List[Dict[str, Any]])
async def list_sessions(service: LiveSonarService = Depends(get_service)):
    """List all registered live sonar sessions."""
    return await service.list_sessions()


@router.get("/sessions/{session_id}", response_model=Dict[str, Any])
async def get_session(
    session_id: str = Path(..., description="The ID of the session"),
    service: LiveSonarService = Depends(get_service),
):
    """Retrieve details and metrics of a live sonar session."""
    sess = await service.get_session(session_id)
    if not sess:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found.")
    return sess


@router.post("/sessions/{session_id}/start")
async def start_session(
    session_id: str = Path(...),
    service: LiveSonarService = Depends(get_service),
):
    """Start live frame acquisition and AI processing."""
    try:
        return await service.start_session(session_id)
    except LiveSonarException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sessions/{session_id}/stop")
async def stop_session(
    session_id: str = Path(...),
    service: LiveSonarService = Depends(get_service),
):
    """Stop live frame acquisition."""
    try:
        return await service.stop_session(session_id)
    except LiveSonarException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions/{session_id}/metrics")
async def get_session_metrics(
    session_id: str = Path(...),
    service: LiveSonarService = Depends(get_service),
):
    """Retrieve real-time streaming and inference metrics."""
    runner = service.get_runner(session_id)
    if not runner:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found.")

    m = runner.session.get_metrics()
    res = runner.latest_result
    return {
        "input_fps": round(m.input_fps, 1),
        "inference_fps": round(res.effective_fps, 1) if res else 0.0,
        "processing_fps": round(m.processing_fps, 1),
        "latency_ms": round(res.latency_breakdown_ms.get("total_ms", 0.0), 1) if res else 0.0,
        "queue_depth": m.queue_depth,
        "frames_received": m.frames_received,
        "frames_processed": m.frames_processed,
        "frames_dropped": m.frames_dropped,
        "drop_rate": round(m.drop_rate, 3),
        "active_tracks_count": len(res.active_tracks) if res else 0,
        "confirmed_targets_count": res.confirmed_targets_count if res else 0,
    }


@router.get("/sessions/{session_id}/tracks")
async def get_session_tracks(
    session_id: str = Path(...),
    service: LiveSonarService = Depends(get_service),
):
    """Retrieve currently active temporal tracks."""
    runner = service.get_runner(session_id)
    if not runner:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found.")

    res = runner.latest_result
    if not res:
        return []

    tracks_out = []
    for t in res.active_tracks:
        tracks_out.append({
            "track_id": t.track_id,
            "class_name": t.class_name,
            "class_id": t.class_id,
            "confidence": round(t.confidence, 3),
            "bbox": {"x": t.bbox[0], "y": t.bbox[1], "w": t.bbox[2], "h": t.bbox[3]},
            "status": t.status,
            "frames_seen": t.frames_seen,
            "first_seen": t.first_seen_utc.isoformat(),
            "last_seen": t.last_seen_utc.isoformat(),
            "trajectory": [{"x": p[0], "y": p[1]} for p in t.trajectory[-30:]],
            "acoustic_shadow": t.acoustic_shadow,
            "latitude": t.latitude,
            "longitude": t.longitude,
            "depth_m": t.depth_m,
        })
    return tracks_out


@router.get("/sessions/{session_id}/detections")
async def get_session_detections(
    session_id: str = Path(...),
    service: LiveSonarService = Depends(get_service),
):
    """Retrieve latest frame detections."""
    runner = service.get_runner(session_id)
    if not runner or not runner.latest_result:
        return []
    return runner.latest_result.detections


@router.get("/sessions/{session_id}/evidence")
async def get_session_evidence(
    session_id: str = Path(...),
    service: LiveSonarService = Depends(get_service),
):
    """Retrieve forensic evidence snapshots captured during session."""
    runner = service.get_runner(session_id)
    if not runner:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found.")
    return runner.evidence_records


@router.post("/sessions/{session_id}/snapshot")
async def capture_manual_snapshot(
    session_id: str = Path(...),
    track_id: Optional[int] = Query(None, description="Optional target track ID to snapshot"),
    service: LiveSonarService = Depends(get_service),
):
    """Manually capture a 4-layer evidence snapshot of the current live frame."""
    runner = service.get_runner(session_id)
    if not runner or not runner.latest_result:
        raise HTTPException(status_code=400, detail="No active frame available for snapshot.")

    res = runner.latest_result
    # Choose target bounding box or full center crop
    bbox = (0, 0, res.raw_image.shape[1], res.raw_image.shape[0])
    cls_name = "manual_snapshot"
    conf = 1.0

    if track_id is not None:
        for t in res.active_tracks:
            if t.track_id == track_id:
                bbox = t.bbox
                cls_name = t.class_name
                conf = t.confidence
                break

    ev = capture_evidence(
        session_id=session_id,
        track_id=track_id or 0,
        frame_id=res.frame_id,
        raw_image=res.raw_image,
        processed_image=res.processed_image,
        bbox=bbox,
        class_name=cls_name,
        confidence=conf,
    )
    runner.evidence_records.append(ev)
    return {"status": "SUCCESS", "evidence": ev}


@router.get("/health", response_model=LiveHealthResponse)
async def get_live_sonar_health(service: LiveSonarService = Depends(get_service)):
    """Truthful health endpoint reporting real device, model, and throughput metrics."""
    return service.get_health()
