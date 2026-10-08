"""SQLAlchemy models for Media Integrity platform."""
import time
from sqlalchemy import (
    Column,
    String,
    Float,
    Integer,
    Boolean,
    Text,
    JSON,
    ForeignKey,
    Index,
)
from sqlalchemy.orm import relationship
from backend.app.database import Base


class Call(Base):
    __tablename__ = "calls"

    id = Column(String(64), primary_key=True, index=True)
    room_id = Column(String(64), index=True, nullable=False)
    title = Column(String(255), default="Forensic Live Call")
    status = Column(String(32), default="active")  # active, completed, terminated
    created_at = Column(Float, default=time.time)
    ended_at = Column(Float, nullable=True)

    participants = relationship("Participant", back_populates="call", cascade="all, delete-orphan")
    risk_events = relationship("RiskEvent", back_populates="call", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="call", cascade="all, delete-orphan")


class Participant(Base):
    __tablename__ = "participants"

    id = Column(String(64), primary_key=True, index=True)
    call_id = Column(String(64), ForeignKey("calls.id"), nullable=False, index=True)
    participant_id = Column(String(64), nullable=False)
    user_name = Column(String(128), default="Participant")
    role = Column(String(32), default="remote")  # local, remote
    joined_at = Column(Float, default=time.time)

    call = relationship("Call", back_populates="participants")


class MediaRecord(Base):
    __tablename__ = "media"

    id = Column(String(64), primary_key=True, index=True)
    sha256 = Column(String(64), unique=True, index=True, nullable=False)
    filename = Column(String(255), nullable=False)
    file_path = Column(Text, nullable=False)
    media_type = Column(String(32), default="video")  # video, audio, image
    duration_seconds = Column(Float, default=0.0)
    size_bytes = Column(Integer, default=0)
    created_at = Column(Float, default=time.time)


class FrameResult(Base):
    __tablename__ = "frame_results"

    id = Column(Integer, primary_key=True, autoincrement=True)
    call_id = Column(String(64), index=True, nullable=False)
    participant_id = Column(String(64), default="remote")
    timestamp = Column(Float, index=True, nullable=False)
    score = Column(Float, nullable=False)
    raw_score = Column(Float, nullable=False)
    calibrated_score = Column(Float, nullable=False)
    status = Column(String(32), default="AUTHENTIC")
    bounding_box = Column(JSON, nullable=True)
    landmarks = Column(JSON, nullable=True)
    model_version = Column(String(64), nullable=False)
    processing_time_ms = Column(Float, default=0.0)

    __table_args__ = (
        Index("idx_frame_call_time", "call_id", "timestamp"),
    )


class AudioResult(Base):
    __tablename__ = "audio_results"

    id = Column(Integer, primary_key=True, autoincrement=True)
    call_id = Column(String(64), index=True, nullable=False)
    participant_id = Column(String(64), default="remote")
    window_start = Column(Float, index=True, nullable=False)
    window_end = Column(Float, nullable=False)
    audio_score = Column(Float, nullable=False)
    raw_score = Column(Float, nullable=False)
    calibrated_score = Column(Float, nullable=False)
    has_speech = Column(Boolean, default=True)
    status = Column(String(32), default="AUTHENTIC")
    model_version = Column(String(64), nullable=False)
    latency_ms = Column(Float, default=0.0)


class TemporalResultRecord(Base):
    __tablename__ = "temporal_results"

    id = Column(Integer, primary_key=True, autoincrement=True)
    call_id = Column(String(64), index=True, nullable=False)
    timestamp = Column(Float, index=True, nullable=False)
    score = Column(Float, nullable=False)
    feature_variance = Column(Float, default=0.0)
    continuity_break = Column(Boolean, default=False)


class AVSyncResultRecord(Base):
    __tablename__ = "av_sync_results"

    id = Column(Integer, primary_key=True, autoincrement=True)
    call_id = Column(String(64), index=True, nullable=False)
    timestamp = Column(Float, index=True, nullable=False)
    av_sync_score = Column(Float, nullable=False)
    contradiction_score = Column(Float, nullable=False)
    mouth_motion_energy = Column(Float, default=0.0)
    audio_energy = Column(Float, default=0.0)


class FusionResultRecord(Base):
    __tablename__ = "fusion_results"

    id = Column(Integer, primary_key=True, autoincrement=True)
    call_id = Column(String(64), index=True, nullable=False)
    timestamp = Column(Float, index=True, nullable=False)
    raw_risk_score = Column(Float, nullable=False)
    calibrated_risk_score = Column(Float, nullable=False)
    risk_state = Column(String(32), default="NORMAL")
    classification = Column(String(32), default="LIKELY_AUTHENTIC")
    uncertainty = Column(Float, default=0.1)


class RiskEvent(Base):
    __tablename__ = "risk_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    event_id = Column(String(64), unique=True, index=True, nullable=False)
    call_id = Column(String(64), ForeignKey("calls.id"), nullable=False, index=True)
    start_time = Column(Float, nullable=False)
    end_time = Column(Float, nullable=False)
    signals = Column(JSON, nullable=False)
    severity = Column(String(32), default="medium")
    agreement = Column(String(32), default="contradiction")
    explanation = Column(Text, nullable=False)
    created_at = Column(Float, default=time.time)

    call = relationship("Call", back_populates="risk_events")


class MediaDNARecord(Base):
    __tablename__ = "media_dna"

    id = Column(Integer, primary_key=True, autoincrement=True)
    media_sha256 = Column(String(64), unique=True, index=True, nullable=False)
    perceptual_hash = Column(String(64), nullable=False)
    audio_fingerprint = Column(Text, nullable=True)
    temporal_fingerprint = Column(Text, nullable=True)
    codec_metadata = Column(JSON, default=dict)
    duration_seconds = Column(Float, default=0.0)
    resolution = Column(String(32), default="unknown")
    frame_rate = Column(Float, default=0.0)
    created_at = Column(Float, default=time.time)


class ProvenanceRecord(Base):
    __tablename__ = "provenance"

    id = Column(Integer, primary_key=True, autoincrement=True)
    media_sha256 = Column(String(64), unique=True, index=True, nullable=False)
    status = Column(String(32), default="C2PA_UNAVAILABLE")
    issuer = Column(String(255), nullable=True)
    claim_generator = Column(String(255), nullable=True)
    signature_valid = Column(Boolean, nullable=True)
    details = Column(JSON, default=dict)
    checked_at = Column(Float, default=time.time)


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    event_id = Column(String(64), unique=True, index=True, nullable=False)
    call_id = Column(String(64), ForeignKey("calls.id"), nullable=False, index=True)
    timestamp = Column(Float, nullable=False)
    event_type = Column(String(64), nullable=False)
    payload_hash = Column(String(64), nullable=False)
    previous_hash = Column(String(64), nullable=False)
    current_hash = Column(String(64), nullable=False)

    call = relationship("Call", back_populates="audit_logs")


class ForensicReportRecord(Base):
    __tablename__ = "reports"

    id = Column(String(64), primary_key=True, index=True)
    call_id = Column(String(64), index=True, nullable=False)
    media_sha256 = Column(String(64), nullable=True)
    final_assessment = Column(String(64), nullable=False)
    calibrated_risk = Column(Float, default=0.0)
    report_json = Column(JSON, nullable=False)
    html_content = Column(Text, nullable=True)
    storage_url = Column(Text, nullable=True)
    created_at = Column(Float, default=time.time)


class BulkJobRecord(Base):
    __tablename__ = "bulk_jobs"

    job_id = Column(String(64), primary_key=True, index=True)
    status = Column(String(32), default="queued")  # queued, processing, completed, failed
    total_files = Column(Integer, default=0)
    processed_files = Column(Integer, default=0)
    results = Column(JSON, default=list)
    storage_url = Column(Text, nullable=True)
    created_at = Column(Float, default=time.time)
    completed_at = Column(Float, nullable=True)

