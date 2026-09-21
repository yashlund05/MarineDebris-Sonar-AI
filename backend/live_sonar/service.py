"""Live Sonar Service & Concurrency Orchestrator.

Manages active live sonar sessions, isolates inference workers and ByteTrack state per session,
orchestrates asynchronous frame processing, and dispatches real-time events.
Conforms to Requirements R1, R2, R3, R5 of ORIGINAL_REQUEST.md.
"""

from __future__ import annotations

import asyncio
import base64
import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional, Set

from backend.config import get_settings
from backend.inference.model_loader import ModelLoader
from backend.live_sonar.models import (
    DropPolicy,
    LiveSonarException,
    LiveSonarSessionConfig,
    LiveSonarStateError,
    SessionStatus,
    StreamMetrics,
)
from backend.live_sonar.pipeline.inference import LiveDetectionResult, LiveInferenceWorker
from backend.live_sonar.pipeline.tracker import LiveTrack
from backend.live_sonar.recording.evidence import capture_evidence
from backend.live_sonar.recording.recorder import SessionRecorder
from backend.live_sonar.session import LiveSonarSession

logger = logging.getLogger(__name__)


class SessionRunner:
    """Combines a streaming session, an isolated inference worker, and a recorder."""

    def __init__(self, session: LiveSonarSession, config: LiveSonarSessionConfig) -> None:
        self.session = session
        self.config = config
        self.session_id = config.session_id

        self.inference_worker = LiveInferenceWorker(
            session_id=self.session_id,
            conf_threshold=config.confidence_threshold,
            target_inference_fps=config.inference_fps,
            preprocessing_profile=config.preprocessing_profile,
            min_confirmed_frames=config.minimum_confirmed_frames,
        )

        self.recorder = SessionRecorder(session_id=self.session_id)
        self.latest_result: Optional[LiveDetectionResult] = None
        self.confirmed_track_ids: Set[int] = set()
        self.evidence_records: List[Dict[str, Any]] = []

        self._consumer_task: Optional[asyncio.Task] = None
        self._listeners: List[Callable[[Dict[str, Any]], Any]] = []
        self._is_running = False

    def add_listener(self, listener: Callable[[Dict[str, Any]], Any]) -> None:
        self._listeners.append(listener)

    def remove_listener(self, listener: Callable[[Dict[str, Any]], Any]) -> None:
        if listener in self._listeners:
            self._listeners.remove(listener)

    async def start(self) -> None:
        """Start both the source adapter ingestion and the AI consumer loop."""
        await self.session.start()
        self._is_running = True

        if self.config.enable_recording:
            self.recorder.start(fps=self.config.target_fps)

        self._consumer_task = asyncio.create_task(
            self._consumer_loop(),
            name=f"live-sonar-ai-{self.session_id}",
        )
        logger.info(f"SessionRunner {self.session_id} started.")

    async def stop(self) -> None:
        """Stop AI loop, recording, and source stream."""
        self._is_running = False
        if self._consumer_task and not self._consumer_task.done():
            self._consumer_task.cancel()
            try:
                await self._consumer_task
            except asyncio.CancelledError:
                pass

        await self.session.stop()
        if self.recorder.is_recording:
            self.recorder.stop()
        logger.info(f"SessionRunner {self.session_id} stopped.")

    async def _consumer_loop(self) -> None:
        """Continuously pops frames from buffer and passes them through AI inference."""
        while self._is_running:
            try:
                # Get next frame from bounded buffer
                frame = await self.session.buffer.get()

                # Process through AI pipeline
                result = await asyncio.to_thread(self.inference_worker.process_frame, frame)
                self.latest_result = result

                # Check if recording is active
                if self.recorder.is_recording:
                    self.recorder.write_frame(frame, result.detections, result.active_tracks)

                # Automatic evidence capture for newly confirmed tracks
                for trk in result.active_tracks:
                    if trk.status == "CONFIRMED" and trk.track_id not in self.confirmed_track_ids:
                        self.confirmed_track_ids.add(trk.track_id)
                        ev = capture_evidence(
                            session_id=self.session_id,
                            track_id=trk.track_id,
                            frame_id=result.frame_id,
                            raw_image=result.raw_image,
                            processed_image=result.processed_image,
                            bbox=trk.bbox,
                            class_name=trk.class_name,
                            confidence=trk.confidence,
                            metadata={
                                "first_seen_utc": trk.first_seen_utc.isoformat(),
                                "last_seen_utc": trk.last_seen_utc.isoformat(),
                                "frames_seen": trk.frames_seen,
                                "acoustic_shadow": trk.acoustic_shadow,
                                "latitude": trk.latitude,
                                "longitude": trk.longitude,
                            },
                        )
                        self.evidence_records.append(ev)

                # Broadcast to WebSocket listeners
                if self._listeners:
                    payload = self.build_websocket_frame_payload(result)
                    for listener in self._listeners:
                        try:
                            if asyncio.iscoroutinefunction(listener):
                                asyncio.create_task(listener(payload))
                            else:
                                listener(payload)
                        except Exception as e:
                            logger.error(f"Error notifying live listener: {e}")

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in AI consumer loop {self.session_id}: {e}")
                await asyncio.sleep(0.01)

    def build_websocket_frame_payload(self, result: LiveDetectionResult) -> Dict[str, Any]:
        """Format detection result into standard WebSocket JSON payload with JPEG preview."""
        metrics = self.session.get_metrics()

        # Format tracks
        tracks_data = []
        for t in result.active_tracks:
            tracks_data.append({
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

        # Base64 preview frame (if available)
        preview_b64 = None
        if result.preview_jpeg is not None:
            preview_b64 = base64.b64encode(result.preview_jpeg).decode("ascii")

        return {
            "type": "frame_result",
            "session_id": self.session_id,
            "frame_id": result.frame_id,
            "sequence_number": result.sequence_number,
            "timestamp_utc": result.timestamp_utc.isoformat(),
            "preview_jpeg": preview_b64,
            "detections": result.detections,
            "tracks": tracks_data,
            "metrics": {
                "input_fps": round(metrics.input_fps, 1),
                "inference_fps": round(result.effective_fps, 1),
                "latency_ms": round(result.latency_breakdown_ms.get("total_ms", 0.0), 1),
                "queue_depth": metrics.queue_depth,
                "frames_dropped": metrics.frames_dropped,
                "drop_rate": round(metrics.drop_rate, 3),
                "active_tracks": len(result.active_tracks),
                "confirmed_targets": result.confirmed_targets_count,
            },
            "sonar_metadata": {
                "frequency_hz": result.sonar_telemetry.frequency_hz if result.sonar_telemetry else None,
                "range_m": result.sonar_telemetry.range_m if result.sonar_telemetry else None,
                "gain_db": result.sonar_telemetry.gain_db if result.sonar_telemetry else None,
            },
            "navigation": {
                "latitude": result.navigation.latitude if result.navigation else None,
                "longitude": result.navigation.longitude if result.navigation else None,
                "heading_deg": result.navigation.heading_deg if result.navigation else None,
                "depth_m": result.navigation.depth_m if result.navigation else None,
            },
        }


class LiveSonarService:
    """Singleton service managing live sonar sessions and API requests."""

    _instance: Optional["LiveSonarService"] = None

    def __init__(self) -> None:
        self._runners: Dict[str, SessionRunner] = {}
        self._lock = asyncio.Lock()

    @classmethod
    def get_instance(cls) -> "LiveSonarService":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    async def create_session(self, config: LiveSonarSessionConfig) -> Dict[str, Any]:
        """Create and register a new live sonar session."""
        async with self._lock:
            if config.session_id in self._runners:
                raise LiveSonarStateError(f"Session {config.session_id} already exists.")

            session = LiveSonarSession(config)
            runner = SessionRunner(session, config)
            self._runners[config.session_id] = runner

            return {
                "session_id": config.session_id,
                "name": config.name,
                "source_type": config.source_type,
                "source_uri": config.source_uri,
                "status": session.status.value,
                "created_at": datetime.now(timezone.utc).isoformat(),
            }

    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve session status, configuration, and telemetry."""
        runner = self._runners.get(session_id)
        if not runner:
            return None

        s = runner.session
        m = s.get_metrics()
        return {
            "session_id": s.session_id,
            "name": runner.config.name,
            "source_type": runner.config.source_type,
            "source_uri": runner.config.source_uri,
            "status": s.status.value,
            "started_at": s.started_at.isoformat() if s.started_at else None,
            "stopped_at": s.stopped_at.isoformat() if s.stopped_at else None,
            "metrics": {
                "input_fps": round(m.input_fps, 1),
                "processing_fps": round(m.processing_fps, 1),
                "queue_depth": m.queue_depth,
                "frames_received": m.frames_received,
                "frames_processed": m.frames_processed,
                "frames_dropped": m.frames_dropped,
                "drop_rate": round(m.drop_rate, 3),
            },
            "is_recording": runner.recorder.is_recording,
            "active_tracks_count": len(runner.latest_result.active_tracks) if runner.latest_result else 0,
            "confirmed_targets_count": runner.latest_result.confirmed_targets_count if runner.latest_result else 0,
        }

    async def list_sessions(self) -> List[Dict[str, Any]]:
        """List all registered sessions."""
        results = []
        for sid in list(self._runners.keys()):
            data = await self.get_session(sid)
            if data:
                results.append(data)
        return results

    async def start_session(self, session_id: str) -> Dict[str, Any]:
        """Start live acquisition and AI processing."""
        runner = self._runners.get(session_id)
        if not runner:
            raise LiveSonarException(f"Session {session_id} not found", status_code=404)
        await runner.start()
        return {"session_id": session_id, "status": runner.session.status.value}

    async def stop_session(self, session_id: str) -> Dict[str, Any]:
        """Stop session cleanly."""
        runner = self._runners.get(session_id)
        if not runner:
            raise LiveSonarException(f"Session {session_id} not found", status_code=404)
        await runner.stop()
        return {"session_id": session_id, "status": runner.session.status.value}

    def get_runner(self, session_id: str) -> Optional[SessionRunner]:
        return self._runners.get(session_id)

    def get_health(self) -> Dict[str, Any]:
        """Report truthful system and model health without fabrication."""
        active_count = sum(1 for r in self._runners.values() if r.session.status == SessionStatus.RUNNING)
        device = ModelLoader.get_device()
        model_status = ModelLoader.get_model_status()

        return {
            "status": "healthy",
            "active_sessions_count": active_count,
            "gpu_available": device == "cuda",
            "inference_device": device,
            "model_status": model_status.get("state", "UNKNOWN"),
            "model_loaded": model_status.get("is_loaded", False),
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        }
