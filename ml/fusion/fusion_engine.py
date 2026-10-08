"""
Multimodal Evidence Fusion Engine.
Aggregates visual, audio, temporal, synchronization, and identity forensic signals.
Handles missing modalities adaptively without false penalties.
"""
from typing import Optional, Dict, Any, Tuple
import numpy as np

from backend.app.config import settings
from backend.app.schemas.contracts import ClassificationState, RiskState


class FusionEngine:
    def __init__(self):
        # Base modality weights (AV sync removed per user requirement)
        self.default_weights = {
            "visual": 0.50,
            "audio": 0.30,
            "temporal": 0.12,
            "identity": 0.08,
        }
        
        self.watch_threshold = settings.WATCH_THRESHOLD
        self.elevated_threshold = settings.ELEVATED_THRESHOLD
        self.high_risk_threshold = settings.HIGH_RISK_THRESHOLD

    def fuse(
        self,
        visual_score: Optional[float] = None,
        audio_score: Optional[float] = None,
        temporal_score: Optional[float] = None,
        av_sync_score: Optional[float] = None,
        identity_similarity: Optional[float] = None,
        model_disagreement: float = 0.0,
        liveness_score: Optional[float] = None,
        stability_score: float = 1.0,
        frame_count: int = 20,
    ) -> Tuple[float, float, ClassificationState, float]:
        """
        Computes (raw_risk_score, calibrated_risk_score, classification, uncertainty).
        Guarantees warmup stabilization for the first 10 frames and applies
        Forensic Severity Envelope so confirmed face-swaps are never averaged out.
        """
        active_weights = {}
        values = {}

        # 1. Visual Anomaly Signal
        if visual_score is not None:
            # Positive biometric liveness attenuation: natural dermal micro-dynamics
            # authenticates human presence against glasses glare / teeth high-frequency noise
            effective_visual = visual_score
            if liveness_score is not None and liveness_score >= 0.75 and effective_visual < 0.85:
                liveness_attenuation = min(0.40, (liveness_score - 0.75) * 1.5)
                effective_visual = max(0.05, round(effective_visual * (1.0 - liveness_attenuation), 4))

            active_weights["visual"] = self.default_weights["visual"]
            values["visual"] = effective_visual

        # 2. Audio Anomaly Signal
        if audio_score is not None:
            active_weights["audio"] = self.default_weights["audio"]
            values["audio"] = audio_score

        # 3. Temporal Anomaly Signal
        if temporal_score is not None:
            active_weights["temporal"] = self.default_weights["temporal"]
            values["temporal"] = temporal_score

        # 4. Identity Inconsistency (mismatch = 1 - similarity)
        if identity_similarity is not None:
            active_weights["identity"] = self.default_weights["identity"]
            values["identity"] = max(0.0, min(1.0, 1.0 - identity_similarity))

        # Handle all missing modalities gracefully
        if not active_weights:
            return 0.0, 0.0, ClassificationState.INCONCLUSIVE, 1.0

        # Renormalize weights to sum to 1.0
        total_weight = sum(active_weights.values())
        normalized_weights = {k: v / total_weight for k, v in active_weights.items()}

        # Compute raw weighted fusion score
        raw_risk_score = sum(values[k] * normalized_weights[k] for k in values)

        # Forensic Severity Envelope:
        # A unanimous high-confidence manipulation signal (e.g. face swap >= 0.70 with dual-model agreement
        # or audio clone >= 0.70) must NEVER be averaged out by low temporal jitter or absence of speech.
        max_modality_risk = max([values.get("visual", 0.0), values.get("audio", 0.0)])
        if max_modality_risk >= 0.70 and model_disagreement < 0.25:
            raw_risk_score = max(raw_risk_score, 0.85 * max_modality_risk + 0.15 * raw_risk_score)

        # Calibrated risk score with logistic adjustment
        calibrated_risk = float(
            1.0 / (1.0 + np.exp(-6.0 * (raw_risk_score - 0.5)))
        )

        # Quantify Uncertainty
        # Uncertainty rises if modalities are missing, models disagree, or during stream warmup
        missing_modality_penalty = (len(self.default_weights) - len(active_weights)) * 0.10
        disagreement_penalty = model_disagreement * 0.35
        instability_penalty = max(0.0, (1.0 - stability_score)) * 0.25
        warmup_penalty = max(0.0, (10 - frame_count) * 0.08) if frame_count < 10 else 0.0
        
        uncertainty = min(1.0, 0.05 + missing_modality_penalty + disagreement_penalty + instability_penalty + warmup_penalty)

        # Determine Classification State (strict warmup protection for first 10 frames)
        if frame_count < 10 or uncertainty > 0.65:
            classification = ClassificationState.INCONCLUSIVE
        elif calibrated_risk >= self.elevated_threshold:
            classification = ClassificationState.LIKELY_MANIPULATED
        elif calibrated_risk <= self.watch_threshold:
            classification = ClassificationState.LIKELY_AUTHENTIC
        else:
            classification = ClassificationState.INCONCLUSIVE

        return (
            round(raw_risk_score, 4),
            round(calibrated_risk, 4),
            classification,
            round(uncertainty, 4),
        )
