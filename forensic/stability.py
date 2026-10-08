"""
Evidence Stability Engine.
Applies controlled forensic stress-testing perturbations to suspect frames to verify artifact persistence.
Distinguishes genuine deepfake artifacts (high stability) from transient codec noise (low stability).
"""
from typing import Dict
import cv2
import numpy as np

from backend.app.schemas.contracts import StabilityResult
from ml.visual.detector import VisualDetector


class StabilityEngine:
    def __init__(self, detector: VisualDetector):
        self.detector = detector

    def apply_transformations(self, face_bgr: np.ndarray) -> Dict[str, np.ndarray]:
        """Generate controlled test perturbations."""
        h, w = face_bgr.shape[:2]
        transforms = {"original": face_bgr}

        # 1. Resize perturbation (downscale to 75% and upscale back)
        down = cv2.resize(face_bgr, (max(16, int(w * 0.75)), max(16, int(h * 0.75))), interpolation=cv2.INTER_AREA)
        transforms["resize"] = cv2.resize(down, (w, h), interpolation=cv2.INTER_LINEAR)

        # 2. JPEG re-compression (Quality = 50)
        encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 50]
        _, encimg = cv2.imencode(".jpg", face_bgr, encode_param)
        transforms["jpeg_compression"] = cv2.imdecode(encimg, 1)

        # 3. Mild Gaussian Noise
        noise = np.random.normal(0, 8, face_bgr.shape).astype(np.float32)
        noisy = np.clip(face_bgr.astype(np.float32) + noise, 0, 255).astype(np.uint8)
        transforms["gaussian_noise"] = noisy

        # 4. Mild Gaussian Blur
        transforms["mild_blur"] = cv2.GaussianBlur(face_bgr, (5, 5), 1.2)

        # 5. Center Crop (90% centered crop resized back)
        crop_h, crop_w = int(h * 0.90), int(w * 0.90)
        start_y, start_x = (h - crop_h) // 2, (w - crop_w) // 2
        crop_region = face_bgr[start_y:start_y+crop_h, start_x:start_x+crop_w]
        transforms["center_crop"] = cv2.resize(crop_region, (w, h))

        return transforms

    def evaluate_stability(self, face_bgr: np.ndarray, base_risk_score: float) -> StabilityResult:
        """
        Runs detector across all transformed versions and evaluates score variance and persistence.
        """
        if face_bgr is None or face_bgr.size == 0:
            return StabilityResult(
                base_score=base_risk_score,
                transformed_scores={},
                variance=0.0,
                stability_score=1.0,
                classification="HIGH",
                stability_adjusted_risk=base_risk_score,
            )

        transforms = self.apply_transformations(face_bgr)
        scores = {}

        for name, trans_img in transforms.items():
            res = self.detector.predict(trans_img)
            scores[name] = round(float(res.calibrated_score), 4)

        score_values = list(scores.values())
        variance = float(np.var(score_values))
        mean_score = float(np.mean(score_values))

        # Stability is high if variance is small across perturbations
        # variance < 0.02 -> stability ~ 1.0; variance > 0.08 -> stability drops
        stability_score = max(0.0, min(1.0, 1.0 - (variance * 10.0)))
        classification = "HIGH" if stability_score >= 0.70 else "LOW"

        # Stability-adjusted risk: if unstable, penalize confidence
        if classification == "LOW":
            adjusted_risk = base_risk_score * 0.70
        else:
            adjusted_risk = max(base_risk_score, mean_score)

        return StabilityResult(
            base_score=round(base_risk_score, 4),
            transformed_scores=scores,
            variance=round(variance, 4),
            stability_score=round(stability_score, 4),
            classification=classification,
            stability_adjusted_risk=round(float(adjusted_risk), 4),
        )
