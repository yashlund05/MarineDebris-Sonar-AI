"""WebSocket Endpoint for Live Sonar Streaming.

Delivers bounded preview frames, detection bounding boxes, active ByteTrack IDs,
and real-time telemetry over WebSocket to connected frontend clients.
Conforms to Requirement R3 of ORIGINAL_REQUEST.md.
"""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Optional
from fastapi import APIRouter, Path, WebSocket, WebSocketDisconnect

from backend.live_sonar.service import LiveSonarService

logger = logging.getLogger(__name__)

ws_router = APIRouter(prefix="/ws", tags=["Live Sonar WebSockets"])


@ws_router.websocket("/live-sonar/{session_id}")
async def live_sonar_websocket(
    websocket: WebSocket,
    session_id: str = Path(..., description="The ID of the live sonar session"),
):
    """Real-time bidirectional WebSocket connection for live sonar feed and controls."""
    await websocket.accept()
    service = LiveSonarService.get_instance()
    runner = service.get_runner(session_id)

    if not runner:
        # If session doesn't exist yet, wait or report error
        logger.warning(f"WebSocket connected for non-existent session {session_id}")
        await websocket.send_json({
            "type": "error",
            "message": f"Session {session_id} not registered. Please create session first.",
        })
        await websocket.close(code=1008, reason="Session not found")
        return

    # Queue to decouple broadcast from socket send
    send_queue: asyncio.Queue = asyncio.Queue(maxsize=10)

    def on_frame_result(payload: dict):
        try:
            if send_queue.full():
                # Drop oldest in queue to favor real-time latency
                try:
                    send_queue.get_nowait()
                except asyncio.QueueEmpty:
                    pass
            send_queue.put_nowait(payload)
        except Exception:
            pass

    runner.add_listener(on_frame_result)

    async def sender_task():
        try:
            while True:
                payload = await send_queue.get()
                await websocket.send_text(json.dumps(payload))
                send_queue.task_done()
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.debug(f"Sender task closed for session {session_id}: {e}")

    sender = asyncio.create_task(sender_task())

    try:
        # Initial greeting event
        await websocket.send_json({
            "type": "session_connected",
            "session_id": session_id,
            "status": runner.session.status.value,
            "source_type": runner.config.source_type,
            "source_uri": runner.config.source_uri,
        })

        # Client command loop (pause, resume, speed, seek, snapshot)
        while True:
            text = await websocket.receive_text()
            try:
                msg = json.loads(text)
                action = msg.get("action")
                if action == "pause":
                    await runner.session.pause()
                    await websocket.send_json({"type": "command_ack", "action": "pause"})
                elif action == "resume":
                    await runner.session.resume()
                    await websocket.send_json({"type": "command_ack", "action": "resume"})
                elif action == "speed" and hasattr(runner.session.adapter, "set_speed"):
                    speed = float(msg.get("value", 1.0))
                    runner.session.adapter.set_speed(speed)
                    await websocket.send_json({"type": "command_ack", "action": "speed", "value": speed})
                elif action == "snapshot":
                    track_id = msg.get("track_id")
                    if runner.latest_result:
                        res = runner.latest_result
                        from backend.live_sonar.recording.evidence import capture_evidence
                        ev = capture_evidence(
                            session_id=session_id,
                            track_id=track_id or 0,
                            frame_id=res.frame_id,
                            raw_image=res.raw_image,
                            processed_image=res.processed_image,
                            bbox=(0, 0, res.raw_image.shape[1], res.raw_image.shape[0]),
                            class_name="snapshot",
                            confidence=1.0,
                        )
                        runner.evidence_records.append(ev)
                        await websocket.send_json({"type": "snapshot_created", "evidence": ev})
            except json.JSONDecodeError:
                pass
            except Exception as e:
                logger.error(f"Error handling WebSocket client command: {e}")

    except WebSocketDisconnect:
        logger.info(f"WebSocket client disconnected from live sonar session {session_id}")
    except Exception as e:
        logger.error(f"WebSocket error on session {session_id}: {e}")
    finally:
        runner.remove_listener(on_frame_result)
        sender.cancel()
        try:
            await sender
        except asyncio.CancelledError:
            pass
