"""Visual detector interface definition."""
from abc import ABC, abstractmethod
import numpy as np
from backend.app.schemas.contracts import DetectionResult


class VisualDetector(ABC):
    """Abstract base class for all visual manipulation detectors."""

    @abstractmethod
    def predict(self, face_image: np.ndarray) -> DetectionResult:
        """
        Analyze a cropped face image (RGB or BGR numpy array) and return a DetectionResult.
        """
        pass
