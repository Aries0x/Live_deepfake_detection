"""
Vision Transformer (ViT-B/16) Visual Manipulation Detector.
Leverages global patch-based self-attention to identify high-frequency GAN boundaries,
diffusion blur, and frequency-domain seam artifacts in cropped faces.
Executes in parallel with EfficientNet-B0 on GPU (RTX 5050 CUDA).
"""
import os
import time
from typing import Optional
import cv2
import numpy as np
import torch
import torch.nn as nn
import torchvision.models as models
import torchvision.transforms as transforms

from backend.app.config import settings, get_active_device
from backend.app.logging_config import get_logger
from backend.app.schemas.contracts import DetectionResult, DetectionStatus
from ml.visual.detector import VisualDetector

logger = get_logger("vit_detector")


class ViTDetector(VisualDetector):
    def __init__(self, device: Optional[str] = None):
        self.device_name = device or get_active_device()
        self.device = torch.device(self.device_name)
        self.model_version = "vit_b_16_v1.0.0"
        
        # Temperature scaling parameter for probability calibration
        self.temperature = 1.40
        
        logger.info("Initializing Vision Transformer (ViT-B/16) detector", device=self.device_name)
        
        try:
            self.model = models.vit_b_16(weights=models.ViT_B_16_Weights.DEFAULT)
        except Exception:
            self.model = models.vit_b_16(weights=None)
            
        # Replace 1000-class head with binary forensics head (Real vs Manipulated)
        in_features = self.model.heads.head.in_features
        self.model.heads.head = nn.Linear(in_features, 2)
        
        # Check for fine-tuned weights
        chk_path = os.path.join(os.path.dirname(__file__), "../checkpoints/fine_tuned_vit_b16.pt")
        if os.path.exists(chk_path):
            try:
                chk = torch.load(chk_path, map_location=self.device)
                self.model.load_state_dict(chk["state_dict"])
                self.model_version = "vit_b_16-finetuned-ff++"
                logger.info("Loaded fine-tuned ViT-B/16 checkpoint", path=chk_path, val_auc=chk.get("val_auc"))
            except Exception as e:
                logger.warning("Failed to load fine-tuned ViT checkpoint, using default weights", error=str(e))

        self.model.to(self.device)
        self.model.eval()
        
        # Preprocessing transform for 224x224 RGB inputs
        self.transform = transforms.Compose([
            transforms.ToPILImage(),
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ])
        
        self._warmup()

    def _warmup(self):
        try:
            dummy = torch.zeros((1, 3, 224, 224), device=self.device)
            with torch.no_grad():
                _ = self.model(dummy)
            logger.info("ViT-B/16 warmed up successfully", device=self.device_name)
        except Exception as e:
            logger.warning("ViT warmup failed, will run lazily", error=str(e))

    def predict(self, face_image: np.ndarray) -> DetectionResult:
        """
        Run self-attention inference on face crop.
        Returns DetectionResult with raw_score, calibrated_score, and latency.
        """
        start_time = time.perf_counter()
        
        if face_image is None or face_image.size == 0:
            return DetectionResult(
                score=0.0,
                raw_score=0.0,
                calibrated_score=0.0,
                model_name="ViT-B/16",
                model_version=self.model_version,
                processing_time_ms=0.0,
                status=DetectionStatus.NO_FACE_DETECTED,
            )

        # Blur / quality check
        gray = cv2.cvtColor(face_image, cv2.COLOR_BGR2GRAY)
        laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
        is_low_quality = laplacian_var < 20.0

        face_rgb = cv2.cvtColor(face_image, cv2.COLOR_BGR2RGB)
        input_tensor = self.transform(face_rgb).unsqueeze(0).to(self.device)

        with torch.no_grad():
            logits = self.model(input_tensor)
            
            raw_logit = (logits[0, 1] - logits[0, 0]).item()
            raw_prob = torch.sigmoid(torch.tensor(raw_logit)).item()
            calibrated_prob = torch.sigmoid(torch.tensor(raw_logit / self.temperature)).item()

        elapsed_ms = (time.perf_counter() - start_time) * 1000.0

        if is_low_quality:
            status = DetectionStatus.LOW_QUALITY
        elif calibrated_prob >= settings.ELEVATED_THRESHOLD:
            status = DetectionStatus.SUSPICIOUS
        else:
            status = DetectionStatus.AUTHENTIC

        return DetectionResult(
            score=round(calibrated_prob, 4),
            raw_score=round(raw_prob, 4),
            calibrated_score=round(calibrated_prob, 4),
            model_name="ViT-B/16",
            model_version=self.model_version,
            processing_time_ms=round(elapsed_ms, 2),
            status=status,
            metadata={"laplacian_variance": round(laplacian_var, 2)},
        )
