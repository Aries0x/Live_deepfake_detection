"""
Voice Activity Detection (VAD) module.
Analyzes audio energy and spectral dynamics to distinguish active speech from ambient silence.
"""
import numpy as np


class VoiceActivityDetector:
    def __init__(self, energy_threshold: float = 0.015, zcr_threshold: float = 0.05):
        self.energy_threshold = energy_threshold
        self.zcr_threshold = zcr_threshold

    def is_speech(self, audio_pcm: np.ndarray) -> bool:
        """
        Determines whether the given audio segment contains voiced speech.
        """
        if audio_pcm is None or len(audio_pcm) == 0:
            return False

        # Calculate Root-Mean-Square (RMS) Energy
        rms = np.sqrt(np.mean(audio_pcm**2))
        if rms < self.energy_threshold:
            return False

        # Calculate Zero Crossing Rate (ZCR)
        zero_crossings = np.sum(np.abs(np.diff(np.sign(audio_pcm)))) / (2 * len(audio_pcm))
        
        # Voiced human speech typically maintains moderate ZCR (not pure DC, not pure high noise)
        return zero_crossings > self.zcr_threshold
