"""Audio anti-spoofing detector interface."""
from abc import ABC, abstractmethod
import numpy as np
from backend.app.schemas.contracts import AudioDetectionResult


class AudioDetector(ABC):
    @abstractmethod
    def predict(
        self,
        audio_pcm: np.ndarray,
        sample_rate: int = 16000,
        window_start: float = 0.0,
        window_end: float = 1.0,
    ) -> AudioDetectionResult:
        """
        Analyze audio window PCM samples and return an AudioDetectionResult.
        """
        pass
