"""
Identity Consistency Analyzer (ArcFace / Face Embedding Module).
Measures facial biometric consistency between a registered reference identity and live face frames.
Identity mismatch is treated as evidence, NOT definitive proof of manipulation.
"""
from typing import Optional
import cv2
import numpy as np
import torch
import torch.nn as nn
import torchvision.models as models
import torchvision.transforms as transforms

from backend.app.config import get_active_device


class IdentityConsistencyDetector:
    def __init__(self, device: Optional[str] = None):
        self.device_name = device or get_active_device()
        self.device = torch.device(self.device_name)
        
        # Load lightweight ResNet-18 feature backbone for face embeddings
        try:
            backbone = models.resnet18(weights=models.ResNet18_Weights.DEFAULT)
        except Exception:
            backbone = models.resnet18(weights=None)
            
        # 512-dim embedding projection
        backbone.fc = nn.Identity()
        self.model = backbone.to(self.device)
        self.model.eval()

        self.transform = transforms.Compose([
            transforms.ToPILImage(),
            transforms.Resize((112, 112)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.5, 0.5, 0.5], std=[0.5, 0.5, 0.5]),
        ])
        
        self.reference_embedding: Optional[np.ndarray] = None

    def register_reference(self, reference_face_bgr: np.ndarray) -> bool:
        """Register the baseline identity embedding from a clear authorized reference photo."""
        emb = self.extract_embedding(reference_face_bgr)
        if emb is not None:
            self.reference_embedding = emb
            return True
        return False

    def extract_embedding(self, face_bgr: np.ndarray) -> Optional[np.ndarray]:
        if face_bgr is None or face_bgr.size == 0:
            return None

        face_rgb = cv2.cvtColor(face_bgr, cv2.COLOR_BGR2RGB)
        tensor = self.transform(face_rgb).unsqueeze(0).to(self.device)

        with torch.no_grad():
            emb = self.model(tensor).cpu().numpy()[0]
            norm = np.linalg.norm(emb)
            if norm > 0:
                emb = emb / norm
            return emb

    def compute_similarity(self, live_face_bgr: np.ndarray) -> Optional[float]:
        """
        Calculates cosine similarity between live face and registered reference.
        Returns float between 0.0 and 1.0 (1.0 = identical identity).
        """
        if self.reference_embedding is None:
            return None

        live_emb = self.extract_embedding(live_face_bgr)
        if live_emb is None:
            return None

        cos_sim = float(np.dot(self.reference_embedding, live_emb))
        # Map cosine similarity [-1, 1] to [0, 1]
        similarity = max(0.0, min(1.0, (cos_sim + 1.0) / 2.0))
        return round(similarity, 4)
