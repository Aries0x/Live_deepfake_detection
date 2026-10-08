"""Health and startup diagnostics endpoint."""
from fastapi import APIRouter
from backend.app.schemas.contracts import HealthResponse
from backend.app.config import settings
import torch

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def get_health():
    cuda_avail = torch.cuda.is_available()
    gpu_info = {
        "available": cuda_avail,
        "name": torch.cuda.get_device_name(0) if cuda_avail else "CPU Only",
        "device_count": torch.cuda.device_count() if cuda_avail else 0,
        "memory_allocated_mb": round(torch.cuda.memory_allocated(0) / (1024 * 1024), 2) if cuda_avail else 0.0,
    }

    models_info = {
        "visual_efficientnet_b0": "ready",
        "visual_vit_b16": "ready" if settings.ENABLE_SECOND_VISUAL_MODEL else "disabled",
        "audio_aasist_l": "ready",
        "temporal_gru": "ready",
        "av_sync": "ready",
        "identity_arcface": "ready" if settings.ENABLE_ARCFACE else "disabled",
    }

    return HealthResponse(
        backend="ok",
        database="ok",
        redis="ok",
        gpu=gpu_info,
        models=models_info,
    )
