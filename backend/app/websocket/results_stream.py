"""
Real-Time Forensic Results WebSocket Router.
Broadcasts continuous RiskUpdate payloads to frontend call interface and dashboard.
"""
import asyncio
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from backend.app.services.gpu_worker import ForensicGPUWorker, normalize_call_id
from backend.app.services.call_manager import CallManager
from backend.app.logging_config import get_logger
from backend.auth.dependencies import authenticate_websocket
from backend.auth.otp import DEV_MODE

logger = get_logger("results_stream")
router = APIRouter()


@router.websocket("/ws/results/{call_id}")
async def results_stream(websocket: WebSocket, call_id: str):
    await websocket.accept()
    user = await authenticate_websocket(websocket)
    if not user and not DEV_MODE:
        await websocket.close(code=1008, reason="Authentication session required")
        return

    norm_call_id = normalize_call_id(call_id)
    worker = ForensicGPUWorker.get_instance()
    call_mgr = CallManager.get_instance()
    active_call = call_mgr.get_call(norm_call_id)
    
    result_queue = asyncio.Queue(maxsize=100)
    worker.add_result_listener(norm_call_id, result_queue)
    logger.info("Results listener connected", call_id=norm_call_id, user_id=user.get("user_id") if user else "dev_guest")

    try:
        while True:
            update = await result_queue.get()
            
            # Record into active call history & audit chain
            if active_call:
                active_call.record_risk_update(update)

            # Send serialized RiskUpdate to browser client
            await websocket.send_text(update.model_dump_json())
    except WebSocketDisconnect:
        worker.remove_result_listener(norm_call_id, result_queue)
        logger.info("Results listener disconnected", call_id=norm_call_id)
    except Exception as e:
        worker.remove_result_listener(norm_call_id, result_queue)
        logger.warning("Results stream error", call_id=norm_call_id, error=str(e))
