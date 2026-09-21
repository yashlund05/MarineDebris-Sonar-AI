"""Schema validation utilities and data contract definitions for Live Sonar testing."""

from typing import Dict, Any, List, Optional
from datetime import datetime


def validate_frame_update_message(payload: Dict[str, Any]) -> List[str]:
    """Validate that a WebSocket frame_update payload adheres to the specification.
    
    Returns a list of validation error strings (empty if valid).
    """
    errors = []
    required_fields = ["event", "session_id", "frame_id", "sequence_number", "timestamp", "metrics"]
    for field in required_fields:
        if field not in payload:
            errors.append(f"Missing top-level field '{field}'")
    
    if payload.get("event") != "frame_update":
        errors.append(f"Expected event 'frame_update', got '{payload.get('event')}'")
    
    if "preview_image" not in payload and "preview_jpeg_b64" not in payload:
        errors.append("Payload must contain 'preview_image' or 'preview_jpeg_b64'")

    # Validate metrics
    metrics = payload.get("metrics", {})
    if not isinstance(metrics, dict):
        errors.append("'metrics' must be a dictionary")
    else:
        metric_fields = ["input_fps", "inference_fps", "latency_ms", "queue_depth"]
        for mf in metric_fields:
            if mf not in metrics:
                errors.append(f"Missing metric '{mf}'")
            elif not isinstance(metrics[mf], (int, float)):
                errors.append(f"Metric '{mf}' must be numeric")

    # Validate detections if present
    detections = payload.get("detections", [])
    if not isinstance(detections, list):
        errors.append("'detections' must be a list")
    else:
        for i, det in enumerate(detections):
            for df in ["class_name", "confidence", "bbox"]:
                if df not in det:
                    errors.append(f"Detection [{i}] missing field '{df}'")
            if "confidence" in det and not (0.0 <= det["confidence"] <= 1.0):
                errors.append(f"Detection [{i}] confidence out of range [0, 1]: {det['confidence']}")

    # Validate tracks if present
    tracks = payload.get("tracks", [])
    if not isinstance(tracks, list):
        errors.append("'tracks' must be a list")
    else:
        for i, trk in enumerate(tracks):
            for tf in ["track_id", "class_name", "confidence", "status", "is_confirmed"]:
                if tf not in trk:
                    errors.append(f"Track [{i}] missing field '{tf}'")
            if "status" in trk and trk["status"] not in ["TENTATIVE", "CONFIRMED", "ACTIVE", "LOST", "COMPLETED"]:
                errors.append(f"Track [{i}] invalid status '{trk['status']}'")

    return errors


def validate_session_event_message(payload: Dict[str, Any]) -> List[str]:
    """Validate that a WebSocket session_event payload adheres to the specification."""
    errors = []
    for field in ["event", "session_id", "timestamp"]:
        if field not in payload:
            errors.append(f"Missing required field '{field}'")

    valid_events = {
        "session_started",
        "session_stopped",
        "connection_lost",
        "connection_restored",
        "detection_created",
        "track_confirmed",
        "track_lost",
        "buffer_warning",
        "processing_degraded",
        "error",
    }
    if payload.get("event") not in valid_events:
        errors.append(f"Unknown or invalid session event: '{payload.get('event')}'")

    return errors


def validate_rest_session_config(config: Dict[str, Any]) -> List[str]:
    """Validate REST session creation body."""
    errors = []
    if not config.get("name"):
        errors.append("Field 'name' cannot be empty")
    
    source_type = config.get("source_type")
    valid_sources = ["replay", "rtsp", "usb", "native_stub"]
    if source_type not in valid_sources:
        errors.append(f"source_type '{source_type}' not in {valid_sources}")

    if not config.get("source_uri"):
        errors.append("Field 'source_uri' cannot be empty")

    target_fps = config.get("target_fps", 15.0)
    if not (1.0 <= target_fps <= 60.0):
        errors.append(f"target_fps must be between 1.0 and 60.0, got {target_fps}")

    profile = config.get("preprocessing_profile", "REALTIME")
    valid_profiles = ["REALTIME", "BALANCED", "QUALITY"]
    if profile not in valid_profiles:
        errors.append(f"preprocessing_profile '{profile}' not in {valid_profiles}")

    drop_policy = config.get("drop_policy", "DROP_OLDEST")
    valid_policies = ["DROP_OLDEST", "FIFO", "DROP_NEWEST", "LATEST"]
    if drop_policy not in valid_policies:
        errors.append(f"drop_policy '{drop_policy}' not in {valid_policies}")

    return errors


def validate_evidence_package(metadata: Dict[str, Any]) -> List[str]:
    """Validate evidence package metadata JSON adhering to traceability invariant."""
    errors = []
    traceability = metadata.get("traceability", metadata)
    required = [
        "session_id",
        "track_id",
        "frame_id",
        "timestamp_utc",
        "source_type",
        "model_checkpoint",
        "preprocessing_profile",
        "class_name",
        "bbox",
    ]
    for field in required:
        if field not in traceability:
            errors.append(f"Evidence metadata missing required traceability field: '{field}'")
    return errors
