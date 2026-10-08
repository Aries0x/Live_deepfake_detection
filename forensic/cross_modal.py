"""
Cross-Modal Evidence & Contradiction Engine.
Correlates independent modalities to detect multimodal agreement or stark contradictions.
Generates structured CrossModalEvent objects with deterministic forensic explanations.
"""
import uuid
from typing import Optional, List
from backend.app.schemas.contracts import CrossModalEvent


class CrossModalEngine:
    def __init__(self, elevated_threshold: float = 0.55):
        self.elevated_threshold = elevated_threshold

    def evaluate(
        self,
        call_id: str,
        current_time: float,
        visual_score: Optional[float] = None,
        audio_score: Optional[float] = None,
        temporal_score: Optional[float] = None,
        av_sync_score: Optional[float] = None,
        identity_similarity: Optional[float] = None,
    ) -> Optional[CrossModalEvent]:
        """
        Evaluates active modalities at timestamp to detect multi-signal anomalies.
        """
        signals: List[str] = []
        is_visual_anomaly = visual_score is not None and visual_score >= self.elevated_threshold
        is_audio_anomaly = audio_score is not None and audio_score >= self.elevated_threshold
        is_temporal_anomaly = temporal_score is not None and temporal_score >= self.elevated_threshold
        is_desync = av_sync_score is not None and av_sync_score < 0.45
        is_identity_mismatch = identity_similarity is not None and identity_similarity < 0.40

        if is_visual_anomaly:
            signals.append("visual_anomaly")
        if is_audio_anomaly:
            signals.append("voice_anomaly")
        if is_temporal_anomaly:
            signals.append("temporal_discontinuity")
        if is_desync:
            signals.append("audio_video_desynchronization")
        if is_identity_mismatch:
            signals.append("identity_mismatch")

        if not signals:
            return None

        event_id = f"EVT-{uuid.uuid4().hex[:8].upper()}"
        start_t = round(max(0.0, current_time - 1.0), 2)
        end_t = round(current_time, 2)

        # Multimodal consensus (synthetic voice + face manipulation)
        if is_visual_anomaly and is_audio_anomaly:
            return CrossModalEvent(
                event_id=event_id,
                call_id=call_id,
                start_time=start_t,
                end_time=end_t,
                signals=signals,
                severity="high",
                agreement="multimodal_consensus",
                explanation=(
                    f"Multimodal convergence detected: Both facial deepfake detector ({visual_score:.2f}) "
                    f"and acoustic anti-spoof model ({audio_score:.2f}) observed simultaneous synthetic manipulation."
                ),
            )

        # Cross-modal contradiction (synthetic voice with out-of-sync visual)
        if is_audio_anomaly and is_desync:
            return CrossModalEvent(
                event_id=event_id,
                call_id=call_id,
                start_time=start_t,
                end_time=end_t,
                signals=signals,
                severity="high",
                agreement="contradiction",
                explanation=(
                    f"Acoustic-visual contradiction: Synthetic voice indicator ({audio_score:.2f}) "
                    f"coincides with abnormal lip motion desynchronization (sync={av_sync_score:.2f})."
                ),
            )

        # Visual anomaly + temporal discontinuity
        if is_visual_anomaly and is_temporal_anomaly:
            return CrossModalEvent(
                event_id=event_id,
                call_id=call_id,
                start_time=start_t,
                end_time=end_t,
                signals=signals,
                severity="high",
                agreement="multimodal_consensus",
                explanation=(
                    f"Visual synthesis artifact: Facial boundary distortion ({visual_score:.2f}) "
                    f"correlates with temporal sequence jitter ({temporal_score:.2f})."
                ),
            )

        # Single anomaly with isolated contradiction
        if is_visual_anomaly and (audio_score is not None and audio_score < 0.25):
            return CrossModalEvent(
                event_id=event_id,
                call_id=call_id,
                start_time=start_t,
                end_time=end_t,
                signals=signals,
                severity="medium",
                agreement="contradiction",
                explanation=(
                    f"Visual manipulation detected ({visual_score:.2f}) while acoustic stream remains bonafide. "
                    "Indicates isolated face swap or video re-enactment."
                ),
            )

        # Default moderate event
        return CrossModalEvent(
            event_id=event_id,
            call_id=call_id,
            start_time=start_t,
            end_time=end_t,
            signals=signals,
            severity="medium",
            agreement="isolated_signal",
            explanation=f"Elevated forensic indicator: {', '.join(signals)} observed.",
        )
