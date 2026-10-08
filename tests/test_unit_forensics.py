"""
Level 1 Unit Tests for Media Integrity Forensics Engine.
Validates hash chains, multimodal fusion, state machine, stability engine, and reports.
"""
import copy
import numpy as np
import pytest

from audit.hash_chain import AuditChainManager
from backend.app.schemas.contracts import (
    RiskState,
    ClassificationState,
    DetectionResult,
    DetectionStatus,
)
from forensic.cross_modal import CrossModalEngine
from forensic.media_dna import MediaDNAEngine
from forensic.stability import StabilityEngine
from forensic.state_machine import RiskStateMachine
from ml.fusion.fusion_engine import FusionEngine
from ml.visual.detector import VisualDetector
from reports.generator import ForensicReportGenerator


class DummyDetector(VisualDetector):
    def __init__(self, score_to_return: float = 0.85):
        self.score_to_return = score_to_return

    def predict(self, face_image: np.ndarray) -> DetectionResult:
        return DetectionResult(
            score=self.score_to_return,
            raw_score=self.score_to_return,
            calibrated_score=self.score_to_return,
            model_name="DummyTestDetector",
            model_version="v0.0.1",
            processing_time_ms=1.0,
            status=DetectionStatus.SUSPICIOUS if self.score_to_return > 0.5 else DetectionStatus.AUTHENTIC,
        )


def test_audit_hash_chain():
    call_id = "CALL-TEST-UNIT-01"
    chain_mgr = AuditChainManager(call_id)

    e1 = chain_mgr.append_event("CALL_CREATED", {"call_id": call_id, "room": "room-1"})
    e2 = chain_mgr.append_event("ANALYSIS_STARTED", {"fps": 5})
    e3 = chain_mgr.append_event("ANOMALY_DETECTED", {"score": 0.88})

    assert len(chain_mgr.chain) == 3
    valid, broken, _, _ = AuditChainManager.verify_chain(chain_mgr.chain)
    assert valid is True
    assert broken is None

    # Test tampering detection: alter payload hash of event 2
    tampered_chain = copy.deepcopy(chain_mgr.chain)
    tampered_chain[1].payload_hash = "0" * 64
    valid_tampered, broken_id, exp, act = AuditChainManager.verify_chain(tampered_chain)
    assert valid_tampered is False
    assert broken_id == e2.event_id


def test_fusion_all_modalities():
    engine = FusionEngine()
    raw, cal, classification, uncertainty = engine.fuse(
        visual_score=0.88,
        audio_score=0.92,
        temporal_score=0.75,
        av_sync_score=0.20,  # low sync = high contradiction (0.80)
        identity_similarity=0.45,  # moderate mismatch (0.55)
        stability_score=0.95,
    )

    assert cal > 0.75
    assert classification == ClassificationState.LIKELY_MANIPULATED
    assert uncertainty < 0.40


def test_fusion_missing_modalities():
    engine = FusionEngine()
    # Video only analysis
    raw_v, cal_v, class_v, uncert_v = engine.fuse(
        visual_score=0.15,
        temporal_score=0.10,
    )
    assert class_v == ClassificationState.LIKELY_AUTHENTIC
    assert cal_v < 0.35

    # Audio only analysis
    raw_a, cal_a, class_a, uncert_a = engine.fuse(
        audio_score=0.85,
    )
    assert class_a == ClassificationState.LIKELY_MANIPULATED
    assert cal_a > 0.65


def test_risk_state_machine():
    sm = RiskStateMachine()
    assert sm.state == RiskState.NORMAL

    # Step into WATCH
    s1 = sm.update(0.40)
    assert s1 == RiskState.WATCH

    # Multiple persistent elevated steps into ELEVATED
    sm.update(0.60)
    s3 = sm.update(0.65)
    assert s3 == RiskState.ELEVATED

    # Sustained high risk with multimodal consensus into HIGH
    sm.update(0.85, multimodal_count=2)
    sm.update(0.88, multimodal_count=2)
    sm.update(0.90, multimodal_count=2)
    s_high = sm.update(0.92, multimodal_count=2)
    assert s_high == RiskState.HIGH

    # Recovery: sustained normal signals
    for _ in range(8):
        sm.update(0.10, dt_seconds=1.0)
    assert sm.state != RiskState.HIGH


def test_media_dna():
    engine = MediaDNAEngine()
    fake_bytes = b"Sample video forensic byte payload"
    sha = engine.compute_sha256(fake_bytes)
    assert len(sha) == 64

    fake_face = np.full((64, 64, 3), 128, dtype=np.uint8)
    p_hash = engine.compute_perceptual_hash(fake_face)
    assert len(p_hash) > 0

    fake_audio = np.sin(np.linspace(0, 100, 16000)).astype(np.float32)
    a_fp = engine.compute_audio_fingerprint(fake_audio)
    assert len(a_fp) > 0


def test_cross_modal_engine():
    engine = CrossModalEngine(elevated_threshold=0.55)

    # Multimodal consensus
    evt = engine.evaluate(
        call_id="CALL-001",
        current_time=18.5,
        visual_score=0.85,
        audio_score=0.90,
    )
    assert evt is not None
    assert evt.severity == "high"
    assert evt.agreement == "multimodal_consensus"
    assert "visual_anomaly" in evt.signals
    assert "voice_anomaly" in evt.signals

    # Contradiction: visual manipulated but audio normal
    evt_contra = engine.evaluate(
        call_id="CALL-001",
        current_time=22.0,
        visual_score=0.88,
        audio_score=0.10,
    )
    assert evt_contra is not None
    assert evt_contra.agreement == "contradiction"


def test_stability_engine():
    detector = DummyDetector(score_to_return=0.85)
    stability = StabilityEngine(detector)
    fake_face = np.full((96, 96, 3), 150, dtype=np.uint8)

    res = stability.evaluate_stability(fake_face, base_risk_score=0.85)
    assert res.classification == "HIGH"
    assert res.stability_score >= 0.80
    assert len(res.transformed_scores) >= 5


def test_report_generator():
    report = ForensicReportGenerator.create_report(
        call_id="CALL-TEST-REP",
        media_sha256="abc123sha",
        final_assessment="LIKELY_MANIPULATED",
        calibrated_risk=0.87,
        metrics={
            "frames_sampled": 50,
            "suspicious_frames": 24,
            "audio_windows_analyzed": 10,
            "voice_anomaly_detected": True,
            "mean_av_sync_score": 0.35,
        },
        model_versions={"visual": "v1.0.0"},
        events=[{
            "start_time": 12.0,
            "end_time": 14.5,
            "severity": "high",
            "signals": ["visual_anomaly", "voice_anomaly"],
            "explanation": "Simultaneous synthetic cues.",
        }],
    )

    assert report["final_assessment"] == "LIKELY_MANIPULATED"
    assert "summary_narrative" in report
    assert len(report["summary_narrative"]) > 0

    # Verify HTML rendering
    html = ForensicReportGenerator.render_html(report)
    assert "<html" in html
    assert "Mandatory Forensic Disclaimer" in html
    assert report["report_id"] in html

    # Verify PDF rendering
    pdf = ForensicReportGenerator.render_pdf(report)
    assert pdf.startswith(b"%PDF")
