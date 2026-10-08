"""
AASIST-L / Spectrogram-based PyTorch Audio Anti-Spoofing Detector.
Detects voice clones, TTS, voice conversion, and synthetic speech anomalies.
Executes on GPU (RTX 5050 CUDA) or CPU fallback.
"""
import os
import time
from typing import Optional
import numpy as np
import torch
import torch.nn as nn
import torchaudio.transforms as T

from backend.app.config import settings, get_active_device
from backend.app.logging_config import get_logger
from backend.app.schemas.contracts import AudioDetectionResult, DetectionStatus
from ml.audio.detector import AudioDetector
from ml.audio.vad import VoiceActivityDetector

logger = get_logger("aasist_detector")


class AASISTLightNet(nn.Module):
    """Lightweight 2D-CNN + GRU model for raw acoustic spectrogram anti-spoofing."""
    def __init__(self):
        super().__init__()
        self.conv = nn.Sequential(
            nn.Conv2d(1, 16, kernel_size=3, padding=1),
            nn.BatchNorm2d(16),
            nn.ReLU(),
            nn.MaxPool2d((2, 2)),
            nn.Conv2d(16, 32, kernel_size=3, padding=1),
            nn.BatchNorm2d(32),
            nn.ReLU(),
            nn.MaxPool2d((2, 2)),
        )
        self.gru = nn.GRU(input_size=32 * 16, hidden_size=64, batch_first=True)
        self.classifier = nn.Linear(64, 2)

    def forward(self, x):
        # x: (batch, 1, n_mels=64, time_steps)
        batch = x.size(0)
        feats = self.conv(x)  # (batch, 32, 16, time_steps // 4)
        # Reshape for GRU: (batch, time_steps // 4, 32 * 16)
        b, c, f, t = feats.size()
        feats = feats.permute(0, 3, 1, 2).contiguous().view(b, t, c * f)
        _, h_n = self.gru(feats)
        logits = self.classifier(h_n.squeeze(0))
        return logits


class AASISTDetector(AudioDetector):
    def __init__(self, device: Optional[str] = None):
        self.device_name = device or get_active_device()
        self.device = torch.device(self.device_name)
        self.model_version = settings.AUDIO_MODEL_VERSION
        self.vad = VoiceActivityDetector()
        
        self.temperature = 1.25

        logger.info("Initializing AASIST-L audio detector", device=self.device_name)
        self.model = AASISTLightNet().to(self.device)

        # Check for fine-tuned weights
        chk_path = os.path.join(os.path.dirname(__file__), "../checkpoints/fine_tuned_aasist.pt")
        if os.path.exists(chk_path):
            try:
                chk = torch.load(chk_path, map_location=self.device)
                self.model.load_state_dict(chk["state_dict"])
                self.model_version = f"{settings.AUDIO_MODEL_VERSION}-finetuned"
                logger.info("Loaded fine-tuned AASIST-L checkpoint", path=chk_path, val_auc=chk.get("val_auc"))
            except Exception as e:
                logger.warning("Failed to load fine-tuned AASIST checkpoint, using base weights", error=str(e))

        self.model.eval()

        self.mel_transform = T.MelSpectrogram(
            sample_rate=16000,
            n_fft=512,
            win_length=400,
            hop_length=160,
            n_mels=64,
        ).to(self.device)

        self._warmup()

    def _warmup(self):
        try:
            dummy_pcm = torch.zeros((1, 16000), device=self.device)
            with torch.no_grad():
                mel = self.mel_transform(dummy_pcm).unsqueeze(1)
                _ = self.model(mel)
            logger.info("AASIST-L warmed up successfully", device=self.device_name)
        except Exception as e:
            logger.warning("Audio detector warmup failed", error=str(e))

    def predict(
        self,
        audio_pcm: np.ndarray,
        sample_rate: int = 16000,
        window_start: float = 0.0,
        window_end: float = 1.0,
    ) -> AudioDetectionResult:
        start_time = time.perf_counter()

        if audio_pcm is None or len(audio_pcm) == 0:
            return AudioDetectionResult(
                audio_score=0.0,
                raw_score=0.0,
                calibrated_score=0.0,
                model_name="AASIST-L",
                model_version=self.model_version,
                window_start=window_start,
                window_end=window_end,
                has_speech=False,
                latency_ms=0.0,
                status=DetectionStatus.NO_SPEECH,
            )

        # Check Voice Activity
        has_speech = self.vad.is_speech(audio_pcm)
        if not has_speech:
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            return AudioDetectionResult(
                audio_score=0.0,
                raw_score=0.0,
                calibrated_score=0.0,
                model_name="AASIST-L",
                model_version=self.model_version,
                window_start=window_start,
                window_end=window_end,
                has_speech=False,
                latency_ms=round(elapsed_ms, 2),
                status=DetectionStatus.NO_SPEECH,
            )

        # Ensure audio has standard 16kHz window length (16000 samples)
        tensor_pcm = torch.tensor(audio_pcm, dtype=torch.float32, device=self.device)
        if tensor_pcm.ndim == 1:
            tensor_pcm = tensor_pcm.unsqueeze(0)
        if tensor_pcm.size(1) < 16000:
            # Pad with zeros
            tensor_pcm = torch.nn.functional.pad(tensor_pcm, (0, 16000 - tensor_pcm.size(1)))
        elif tensor_pcm.size(1) > 16000:
            tensor_pcm = tensor_pcm[:, :16000]

        with torch.no_grad():
            mel = self.mel_transform(tensor_pcm).unsqueeze(1)
            logits = self.model(mel)
            
            raw_logit = (logits[0, 1] - logits[0, 0]).item()
            raw_prob = torch.sigmoid(torch.tensor(raw_logit)).item()
            calibrated_prob = torch.sigmoid(torch.tensor(raw_logit / self.temperature)).item()

        elapsed_ms = (time.perf_counter() - start_time) * 1000.0
        status = (
            DetectionStatus.SUSPICIOUS
            if calibrated_prob >= settings.ELEVATED_THRESHOLD
            else DetectionStatus.AUTHENTIC
        )

        return AudioDetectionResult(
            audio_score=round(calibrated_prob, 4),
            raw_score=round(raw_prob, 4),
            calibrated_score=round(calibrated_prob, 4),
            model_name="AASIST-L",
            model_version=self.model_version,
            window_start=round(window_start, 2),
            window_end=round(window_end, 2),
            has_speech=True,
            latency_ms=round(elapsed_ms, 2),
            status=status,
        )
