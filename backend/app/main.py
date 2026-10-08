"""
Media Integrity / SecureCall FastAPI Main Application.
Unified WebRTC signaling, WebSocket media ingestion, and REST API platform.
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.app.config import settings
from backend.app.database import init_db
from backend.app.logging_config import configure_logging, get_logger
from backend.app.services.gpu_worker import ForensicGPUWorker

# Import API Routers
from backend.app.api.health import router as health_router
from backend.app.api.calls import router as calls_router
from backend.app.api.bulk import router as bulk_router
from backend.app.api.models_api import router as models_router
from backend.auth.routes import router as auth_router

# Import WebSocket Routers
from backend.app.websocket.signaling import router as signaling_ws_router
from backend.app.websocket.video_stream import router as video_ws_router
from backend.app.websocket.audio_stream import router as audio_ws_router
from backend.app.websocket.results_stream import router as results_ws_router

configure_logging(log_level="DEBUG" if settings.DEBUG else "INFO")
logger = get_logger("main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing Media Integrity Platform...", app_env=settings.APP_ENV)
    # Initialize SQLite / PostgreSQL Database Tables
    await init_db()
    
    # Launch GPU Inference Worker
    worker = ForensicGPUWorker.get_instance()
    await worker.start()
    
    # Print Dev Credentials banner for easy evaluation
    from backend.auth.otp import DEV_MODE
    from backend.auth.totp import get_current_totp_code
    from backend.auth.models import DEMO_TOTP_SECRET
    if DEV_MODE:
        cur_totp = get_current_totp_code(DEMO_TOTP_SECRET)
        border = "=" * 65
        print(f"\n{border}")
        print("[SECURECALL RBAC & AUTHENTICATION SUBSYSTEM READY - DEV_MODE]")
        print("   Citizen:          citizen@demo.com     (OTP: 123456)")
        print(f"   Forensic Officer: officer@court.demo   / Demo@1234 (TOTP: {cur_totp})")
        print(f"   Judge:            judge@court.demo     / Demo@1234 (TOTP: {cur_totp})")
        print(f"   Admin:            admin@securecall.demo/ Demo@1234 (TOTP: {cur_totp})")
        print(f"{border}\n")

    logger.info("Platform startup complete. Ready for real-time live forensics & RBAC auth.")
    yield
    
    logger.info("Shutting down platform services...")
    await worker.stop()
    logger.info("Platform shutdown complete.")


app = FastAPI(
    title=settings.APP_NAME,
    description="Real-Time Multimodal Media Forensics, Live Call Verification, and RBAC Platform",
    version="1.0.0",
    lifespan=lifespan,
)

# Configure Cross-Origin Resource Sharing (CORS) with credentials support for local and LAN devices
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ],
    allow_origin_regex=r"https?://.*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error("Unhandled server exception", path=request.url.path, error=str(exc))
    return JSONResponse(
        status_code=500,
        content={
            "code": "INTERNAL_SERVER_ERROR",
            "message": "An unexpected error occurred in the media forensics pipeline.",
            "details": str(exc),
            "request_id": str(request.headers.get("x-request-id", "unknown")),
        },
    )


# Register REST API routers
app.include_router(auth_router, tags=["Authentication & RBAC"])
app.include_router(auth_router, prefix=settings.API_PREFIX, tags=["Authentication & RBAC"])
app.include_router(health_router, prefix=settings.API_PREFIX, tags=["Health"])
app.include_router(calls_router, prefix=settings.API_PREFIX, tags=["Calls"])
app.include_router(bulk_router, prefix=settings.API_PREFIX, tags=["Bulk Verification"])
app.include_router(models_router, prefix=settings.API_PREFIX, tags=["Models & Metrics"])

# Register WebSocket routers
app.include_router(signaling_ws_router, tags=["WebRTC Signaling"])
app.include_router(video_ws_router, tags=["Video Analysis Stream"])
app.include_router(audio_ws_router, tags=["Audio Analysis Stream"])
app.include_router(results_ws_router, tags=["Results Broadcast Stream"])


@app.get("/")
async def root():
    return {
        "product": settings.APP_NAME,
        "status": "OPERATIONAL",
        "docs_url": "/docs",
        "health_url": f"{settings.API_PREFIX}/health",
    }
