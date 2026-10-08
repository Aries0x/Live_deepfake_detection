"""
Parallel Dual-Model Visual Forensics Ensemble (EfficientNet-B0 + ViT-B/16).
Executes both convolutional and attention-based visual models concurrently.
Quantifies model disagreement to compute empirical uncertainty.
"""
from typing import Tuple, Optional
import numpy as np

from backend.app.schemas.contracts import DetectionResult, DetectionStatus
from ml.visual.detector import VisualDetector
from ml.visual.efficientnet_detector import EfficientNetDetector
from ml.visual.vit_detector import ViTDetector


class ParallelVisualEnsemble(VisualDetector):
    def __init__(self, enable_vit: bool = True):
        self.efficientnet = EfficientNetDetector()
        self.enable_vit = enable_vit
        self.vit: Optional[ViTDetector] = ViTDetector() if enable_vit else None

    def predict(self, face_image: np.ndarray) -> DetectionResult:
        """Standard VisualDetector interface returning the primary consensus result."""
        primary_res, _, _, _ = self.predict_parallel(face_image)
        return primary_res

    def predict_parallel(
        self, face_image: np.ndarray
    ) -> Tuple[DetectionResult, DetectionResult, Optional[DetectionResult], float]:
        """
        Runs EfficientNet-B0 and ViT-B/16 on the face crop.
        Returns:
            (consensus_result, efficientnet_result, vit_result, model_disagreement)
        """
        # 1. Run EfficientNet-B0
        eff_res = self.efficientnet.predict(face_image)

        # 2. If ViT disabled or unavailable, return single-model verdict
        if not self.enable_vit or self.vit is None:
            return eff_res, eff_res, None, 0.0

        # 3. Run Vision Transformer (ViT-B/16)
        vit_res = self.vit.predict(face_image)

        # 4. Measure Inter-Model Disagreement [0.0, 1.0]
        disagreement = abs(eff_res.calibrated_score - vit_res.calibrated_score)

        # 5. Weighted Consensus (Convolutional local inductive bias + Transformer global attention)
        if eff_res.calibrated_score >= 0.75 and vit_res.calibrated_score >= 0.75:
            # High-confidence deepfake consensus (both models agree)
            consensus_score = round(0.50 * eff_res.calibrated_score + 0.50 * vit_res.calibrated_score, 4)
            raw_consensus = round(0.50 * eff_res.raw_score + 0.50 * vit_res.raw_score, 4)
        elif disagreement >= 0.20 and vit_res.calibrated_score <= 0.55:
            # Models disagree: CNN fired on local high frequencies (e.g. glasses glare, smile/teeth),
            # while ViT global attention verified the face structure is authentic. Prioritize ViT.
            consensus_score = round(0.20 * eff_res.calibrated_score + 0.80 * vit_res.calibrated_score, 4)
            raw_consensus = round(0.20 * eff_res.raw_score + 0.80 * vit_res.raw_score, 4)
        else:
            consensus_score = round(0.50 * eff_res.calibrated_score + 0.50 * vit_res.calibrated_score, 4)
            raw_consensus = round(0.50 * eff_res.raw_score + 0.50 * vit_res.raw_score, 4)
        total_time_ms = round(eff_res.processing_time_ms + vit_res.processing_time_ms, 2)

        # Status determination
        if eff_res.status == DetectionStatus.LOW_QUALITY or vit_res.status == DetectionStatus.LOW_QUALITY:
            status = DetectionStatus.LOW_QUALITY
        elif consensus_score >= 0.55:
            status = DetectionStatus.SUSPICIOUS
        else:
            status = DetectionStatus.AUTHENTIC

        consensus_result = DetectionResult(
            score=consensus_score,
            raw_score=raw_consensus,
            calibrated_score=consensus_score,
            model_name="Ensemble (EfficientNet-B0 + ViT-B/16)",
            model_version=f"{eff_res.model_version}+{vit_res.model_version}",
            processing_time_ms=total_time_ms,
            status=status,
            metadata={
                "efficientnet_score": eff_res.calibrated_score,
                "vit_score": vit_res.calibrated_score,
                "disagreement": round(disagreement, 4),
            },
        )

        return consensus_result, eff_res, vit_res, round(disagreement, 4)
