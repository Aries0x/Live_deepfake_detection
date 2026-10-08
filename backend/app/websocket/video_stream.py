"""
Real-Time Video Analysis WebSocket Router.
Ingests remote video JPEG frames at ~5 FPS and routes into GPU worker bounded queue.
"""
import base64
import time
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from backend.app.services.gpu_worker import ForensicGPUWorker, normalize_call_id
from backend.app.logging_config import get_logger
from backend.auth.dependencies import authenticate_websocket
from backend.auth.otp import DEV_MODE

logger = get_logger("video_stream")
router = APIRouter()


@router.websocket("/ws/analyze/video/{call_id}")
async def video_analysis_stream(websocket: WebSocket, call_id: str):
    await websocket.accept()
    user = await authenticate_websocket(websocket)
    if not user and not DEV_MODE:
        await websocket.close(code=1008, reason="Authentication session required")
        return

    norm_call_id = normalize_call_id(call_id)
    worker = ForensicGPUWorker.get_instance()
    logger.info("Video analysis WebSocket connected", call_id=norm_call_id, user_id=user.get("user_id") if user else "dev_guest")

    try:
        while True:
            # Accepts binary JPEG frame or JSON with base64 encoded frame
            message = await websocket.receive()
            if message.get("type") == "websocket.disconnect":
                break

            ts = time.time()
            participant_id = "remote"

            if "bytes" in message and message["bytes"]:
                frame_bytes = message["bytes"]
                worker.enqueue_video_frame(norm_call_id, participant_id, frame_bytes, ts)

            elif "text" in message and message["text"]:
                try:
                    import json
                    data = json.loads(message["text"])
                    b64_data = data.get("frame")
                    if b64_data:
                        if "," in b64_data:
                            b64_data = b64_data.split(",")[1]
                        frame_bytes = base64.b64decode(b64_data)
                        frame_ts = data.get("timestamp", ts)
                        part_id = data.get("participant_id", participant_id)
                        is_obs_flag = data.get("is_obs")
                        source_device = data.get("source_device") or data.get("source_label")
                        worker.enqueue_video_frame(
                            norm_call_id,
                            part_id,
                            frame_bytes,
                            frame_ts,
                            is_obs=is_obs_flag,
                            source_device=source_device,
                        )
                except Exception as e:
                    logger.warning("Error decoding video JSON message", error=str(e))

    except (WebSocketDisconnect, RuntimeError):
        logger.info("Video analysis WebSocket disconnected", call_id=norm_call_id)
    except Exception as e:
        logger.warning("Video analysis WebSocket error", call_id=norm_call_id, error=str(e))
