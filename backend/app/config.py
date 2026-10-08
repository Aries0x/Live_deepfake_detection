"""
Configuration management for Media Integrity / SecureCall platform.
Supports environment variables and .env configuration with graceful fallbacks.
"""
import os
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    APP_NAME: str = "Media Integrity / SecureCall"
    APP_ENV: str = "development"
    DEBUG: bool = True
    API_PREFIX: str = "/api/v1"
    SECRET_KEY: str = "media-integrity-development-secret-key-32-chars-minimum"
    
    # Device and Hardware Acceleration
    # "cuda", "cpu", or "auto"
    DEVICE: str = "auto"
    
    # Database and Caching
    # Defaults to SQLite async for zero-dependency local dev; can be set to postgresql+asyncpg://...
    DATABASE_URL: str = Field(default="sqlite+aiosqlite:///./forensics.db")
    REDIS_URL: Optional[str] = "redis://localhost:6379/0"

    # Supabase Integration
    SUPABASE_URL: Optional[str] = Field(default=None)
    SUPABASE_PUBLISHABLE_KEY: Optional[str] = Field(default=None)
    SUPABASE_SERVICE_ROLE_KEY: Optional[str] = Field(default=None)
    SUPABASE_STORAGE_BUCKET: str = Field(default="forensic-reports")
    
    # Live Media Ingestion & Sampling Parameters
    VIDEO_SAMPLE_FPS: int = 5
    AUDIO_WINDOW_SECONDS: float = 1.0
    AUDIO_HOP_SECONDS: float = 0.5
    MAX_VIDEO_QUEUE_SIZE: int = 30
    MAX_AUDIO_QUEUE_SIZE: int = 60
    
    # Feature Flags & Auxiliary Modules
    ENABLE_ARCFACE: bool = True
    ENABLE_SECOND_VISUAL_MODEL: bool = True
    ENABLE_SECOND_AUDIO_MODEL: bool = False
    ENABLE_C2PA: bool = True
    ENABLE_STABILITY_TEST: bool = True
    ENABLE_HEAVY_MODELS: bool = True
    HEAVY_MODEL_TRIGGER: float = 0.60
    
    # Risk Classification Thresholds
    WATCH_THRESHOLD: float = 0.35
    ELEVATED_THRESHOLD: float = 0.55
    HIGH_RISK_THRESHOLD: float = 0.75
    
    # Continuous Risk State Machine Timers & Windows
    MIN_SUSPICIOUS_WINDOWS: int = 2
    MIN_MULTIMODAL_AGREEMENT: int = 2
    HIGH_RISK_DURATION: float = 2.0
    RECOVERY_DURATION: float = 4.0
    
    # Security & Storage Limits
    MAX_UPLOAD_MB: int = 100
    MAX_VIDEO_SECONDS: int = 300
    RETENTION_MODE: str = "ephemeral"  # "ephemeral" or "24h"
    DEMO_MODE: bool = False
    
    # Model Versions
    VISUAL_MODEL_VERSION: str = "efficientnet_b0_v1.0.0"
    AUDIO_MODEL_VERSION: str = "aasist_l_v1.0.0"
    TEMPORAL_MODEL_VERSION: str = "temporal_gru_v1.0.0"
    AVSYNC_MODEL_VERSION: str = "syncnet_mouth_v1.0.0"
    FUSION_MODEL_VERSION: str = "calibrated_multimodal_v1.0.0"
    
    # Hugging Face Explainable AI (XAI) Reasoning Model Configuration
    HF_TOKEN: Optional[str] = Field(default=None)
    HF_REASONING_MODEL: str = Field(default="meta-llama/Llama-3.3-70B-Instruct-Turbo")
    HF_ROUTER_URL: str = Field(default="https://router.huggingface.co/together/v1/chat/completions")
    
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()


def get_active_device() -> str:
    """Resolve active computing device ('cuda' or 'cpu')."""
    if settings.DEVICE.lower() == "cpu":
        return "cpu"
    try:
        import torch
        if torch.cuda.is_available():
            return "cuda"
    except Exception:
        pass
    return "cpu"
