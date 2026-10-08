"""
Pydantic data contracts for Media Integrity / SecureCall platform.
Adheres strictly to the specification in MASTER_BUILD_PROMPT_MEDIA_FORENSICS.
"""
from enum import Enum
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


class DetectionStatus(str, Enum):
    AUTHENTIC = "AUTHENTIC"
    SUSPICIOUS = "SUSPICIOUS"
    NOT_APPLICABLE = "NOT_APPLICABLE"
    NO_FACE_DETECTED = "NO_FACE_DETECTED"
    NO_SPEECH = "NO_SPEECH"
    LOW_QUALITY = "LOW_QUALITY"
    ERROR = "ERROR"


class RiskState(str, Enum):
    NORMAL = "NORMAL"
    WATCH = "WATCH"
    ELEVATED = "ELEVATED"
    HIGH = "HIGH"


class ClassificationState(str, Enum):
    LIKELY_AUTHENTIC = "LIKELY_AUTHENTIC"
    INCONCLUSIVE = "INCONCLUSIVE"
    LIKELY_MANIPULATED = "LIKELY_MANIPULATED"


class DetectionResult(BaseModel):
    """Visual deepfake detection result for a single frame or face crop."""
    model_config = {"protected_namespaces": ()}

    score: float = Field(..., ge=0.0, le=1.0, description="Calibrated manipulation probability")
    raw_score: float = Field(..., description="Raw model logit or uncalibrated sigmoid score")
    calibrated_score: float = Field(..., ge=0.0, le=1.0, description="Calibrated score after temperature scaling")
    model_name: str
    model_version: str
    processing_time_ms: float
    status: DetectionStatus = DetectionStatus.AUTHENTIC
    bounding_box: Optional[List[int]] = Field(default=None, description="[x, y, w, h] of face region")
    landmarks: Optional[List[List[float]]] = Field(default=None, description="Keypoints [[x, y], ...]")
    track_id: Optional[str] = "track_0"
    metadata: Dict[str, Any] = Field(default_factory=dict)


class FaceTrack(BaseModel):
    """Representation of an individual tracked face in multi-face scenarios."""
    track_id: str
    bbox: List[int]
    confidence: float
    landmarks: Optional[List[List[float]]] = None
    visual_score: Optional[float] = None
    identity_score: Optional[float] = None
    temporal_score: Optional[float] = None


class AudioDetectionResult(BaseModel):
    """Audio anti-spoofing detection result for an audio window."""
    model_config = {"protected_namespaces": ()}

    audio_score: float = Field(..., ge=0.0, le=1.0, description="Synthetic voice probability (high = synthetic)")
    raw_score: float = Field(..., description="Raw model output")
    calibrated_score: float = Field(..., ge=0.0, le=1.0)
    model_name: str = "AASIST-L"
    model_version: str
    window_start: float
    window_end: float
    has_speech: bool = True
    latency_ms: float
    status: DetectionStatus = DetectionStatus.AUTHENTIC


class SyncResult(BaseModel):
    """Audio-visual synchronization result. High av_sync_score = normal in-sync speech."""
    av_sync_score: float = Field(..., ge=0.0, le=1.0, description="1.0 = perfectly synced, 0.0 = completely asynchronous")
    contradiction_score: float = Field(..., ge=0.0, le=1.0, description="1 - av_sync_score")
    mouth_motion_energy: float
    audio_energy: float
    offset_ms: float = 0.0
    status: str = "OK"


class TemporalResult(BaseModel):
    """Temporal frame-to-frame continuity result."""
    temporal_anomaly_score: float = Field(..., ge=0.0, le=1.0, description="High score = flickering, warping, or discontinuity")
    feature_variance: float
    continuity_break: bool = False
    status: str = "OK"


class CrossModalEvent(BaseModel):
    """Structured event capturing multi-modal contradiction or agreement."""
    event_id: str
    call_id: str
    start_time: float
    end_time: float
    signals: List[str]
    severity: str = "medium"  # low, medium, high
    agreement: str = "contradiction"  # contradiction, multimodal_consensus
    explanation: str


class RiskUpdate(BaseModel):
    """Continuous stream payload broadcast to frontend over WebSocket."""
    type: str = "risk_update"
    call_id: str
    participant_id: str
    timestamp: float
    visual: Optional[float] = Field(default=None, description="Visual anomaly score (0-1)")
    audio: Optional[float] = Field(default=None, description="Audio anomaly score (0-1)")
    temporal: Optional[float] = Field(default=None, description="Temporal anomaly score (0-1)")
    av_sync: Optional[float] = Field(default=None, description="Audio-video sync score (0-1, 1 = synced)")
    identity_similarity: Optional[float] = Field(default=None, description="Identity similarity (0-1, 1 = matched)")
    frequency_artifacts: Optional[float] = Field(default=None, description="2D FFT frequency spectrum anomaly (0-1)")
    model_disagreement: Optional[float] = Field(default=None, description="Disagreement between CNN and ViT models (0-1)")
    liveness_score: Optional[float] = Field(default=None, description="Facial micro-dynamics and biometric liveness (0-1, 1 = natural)")
    raw_risk_score: float
    calibrated_risk_score: float
    risk_state: RiskState = RiskState.NORMAL
    classification: ClassificationState = ClassificationState.LIKELY_AUTHENTIC
    uncertainty: float = 0.1
    active_event: Optional[CrossModalEvent] = None
    dropped_frames: int = 0
    processing_latency_ms: float = 0.0
    is_obs: Optional[bool] = Field(default=None, description="Whether stream originated from OBS / virtual camera / screen capture")
    source_device: Optional[str] = Field(default=None, description="Hardware or virtual source device label")


class MediaDNA(BaseModel):
    """Forensic fingerprint / Media DNA representation."""
    media_sha256: str
    perceptual_hash: str
    audio_fingerprint: Optional[str] = None
    temporal_fingerprint: Optional[str] = None
    codec_metadata: Dict[str, Any] = Field(default_factory=dict)
    duration_seconds: float = 0.0
    resolution: str = "unknown"
    frame_rate: float = 0.0


class C2PAValidation(BaseModel):
    """C2PA / Provenance manifest validation record."""
    status: str = "C2PA_UNAVAILABLE"  # C2PA_PRESENT, C2PA_VALID, C2PA_INVALID, C2PA_UNAVAILABLE
    issuer: Optional[str] = None
    claim_generator: Optional[str] = None
    signature_valid: Optional[bool] = None
    details: Dict[str, Any] = Field(default_factory=dict)


class StabilityResult(BaseModel):
    """Evidence stress-test stability evaluation."""
    base_score: float
    transformed_scores: Dict[str, float] = Field(default_factory=dict)
    variance: float = 0.0
    stability_score: float = 1.0  # 1.0 = highly stable under transforms
    classification: str = "HIGH"  # "HIGH", "LOW"
    stability_adjusted_risk: float


class AuditLogEvent(BaseModel):
    """Tamper-evident hash chain block."""
    event_id: str
    timestamp: float
    event_type: str
    call_id: str
    payload_hash: str
    previous_hash: str
    current_hash: str


class CallCreateRequest(BaseModel):
    room_id: Optional[str] = None
    title: Optional[str] = "Live Forensic Verification Session"
    created_by: Optional[str] = "Analyst"


class CallResponse(BaseModel):
    call_id: str
    room_id: str
    created_at: float
    status: str = "active"


class HealthResponse(BaseModel):
    backend: str = "ok"
    database: str = "ok"
    redis: str = "ok"
    gpu: Dict[str, Any]
    models: Dict[str, str]


class BulkVerificationJob(BaseModel):
    job_id: str
    created_at: float
    status: str = "pending"  # pending, processing, completed, failed
    total_files: int = 0
    processed_files: int = 0
    results: List[Dict[str, Any]] = Field(default_factory=list)


class TimelineSegment(BaseModel):
    start_sec: float
    end_sec: float
    confidence: float
    label: str = "FAKE"
    reason: str = "High-frequency facial seam artifacts & temporal discontinuity detected"


class FrameEvidenceItem(BaseModel):
    frame_index: int
    timestamp_sec: float
    fake_score: float
    heatmap_path: Optional[str] = None


class EvidenceBundle(BaseModel):
    video_id: str
    video_path: str
    fps: float
    total_frames: int
    overall_fake_score: float
    overall_label: str  # "FAKE" or "REAL"
    processing_time_ms: int
    segments: List[TimelineSegment] = Field(default_factory=list)
    frame_data: List[FrameEvidenceItem] = Field(default_factory=list)

