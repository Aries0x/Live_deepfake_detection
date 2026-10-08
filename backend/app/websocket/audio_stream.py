"""
Real-Time Audio Analysis WebSocket Router.
Ingests remote audio PCM chunks from browser AudioWorklet and routes into GPU worker bounded queue.
"""
import time
import numpy as np
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from backend.app.services.gpu_worker import ForensicGPUWorker, normalize_call_id
from backend.app.logging_config import get_logger
from backend.auth.dependencies import authenticate_websocket
from backend.auth.otp import DEV_MODE

logger = get_logger("audio_stream")
router = APIRouter()


@router.websocket("/ws/analyze/audio/{call_id}")
async def audio_analysis_stream(websocket: WebSocket, call_id: str):
    await websocket.accept()
    user = await authenticate_websocket(websocket)
    if not user and not DEV_MODE:
        await websocket.close(code=1008, reason="Authentication session required")
        return

    norm_call_id = normalize_call_id(call_id)
    worker = ForensicGPUWorker.get_instance()
    logger.info("Audio analysis WebSocket connected", call_id=norm_call_id, user_id=user.get("user_id") if user else "dev_guest")

    try:
        while True:
            message = await websocket.receive()
            if message.get("type") == "websocket.disconnect":
                break

            ts = time.time()
            participant_id = "remote"

            if "bytes" in message and message["bytes"]:
                raw_bytes = message["bytes"]
                pcm_data = np.frombuffer(raw_bytes, dtype=np.float32)
                worker.enqueue_audio_chunk(norm_call_id, participant_id, pcm_data, ts)

            elif "text" in message and message["text"]:
                import json
                try:
                    data = json.loads(message["text"])
                    samples = data.get("samples")
                    if samples is not None:
                        pcm_data = np.array(samples, dtype=np.float32)
                        chunk_ts = data.get("timestamp", ts)
                        part_id = data.get("participant_id", participant_id)
                        worker.enqueue_audio_chunk(norm_call_id, part_id, pcm_data, chunk_ts)
                except Exception as e:
                    logger.warning("Error decoding audio JSON message", error=str(e))

    except (WebSocketDisconnect, RuntimeError):
        logger.info("Audio analysis WebSocket disconnected", call_id=norm_call_id)
    except Exception as e:
        logger.warning("Audio analysis WebSocket error", call_id=norm_call_id, error=str(e))
