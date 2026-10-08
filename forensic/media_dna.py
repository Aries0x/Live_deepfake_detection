"""
Media DNA & Forensic Fingerprinting Module.
Generates multi-layered media identifiers:
- Cryptographic SHA-256 hash of media bytes
- Perceptual visual hash (dHash) for cross-platform visual matching
- Acoustic spectral fingerprint
- Temporal cadence fingerprint
"""
import hashlib
from typing import Optional, Dict, Any
import cv2
import numpy as np

from backend.app.schemas.contracts import MediaDNA


class MediaDNAEngine:
    @staticmethod
    def compute_sha256(media_bytes: bytes) -> str:
        """Computes cryptographic SHA-256 digest of media byte stream."""
        return hashlib.sha256(media_bytes).hexdigest()

    @staticmethod
    def compute_perceptual_hash(image_bgr: np.ndarray) -> str:
        """
        Computes 64-bit difference hash (dHash) of image frame.
        Robust against scaling, color shifts, and compression.
        """
        if image_bgr is None or image_bgr.size == 0:
            return "0000000000000000"

        # Resize to 9x8 and convert to grayscale
        resized = cv2.resize(image_bgr, (9, 8), interpolation=cv2.INTER_AREA)
        gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)
        
        # Compare adjacent pixels in each row
        diff = gray[:, 1:] > gray[:, :-1]
        
        # Convert boolean matrix to 64-bit hexadecimal string
        hex_str = "".join([f"{int(b):x}" for b in diff.flatten()])
        return hex_str

    @staticmethod
    def compute_audio_fingerprint(audio_pcm: np.ndarray, sample_rate: int = 16000) -> str:
        """
        Computes acoustic peak spectral fingerprint from audio PCM buffer.
        """
        if audio_pcm is None or len(audio_pcm) == 0:
            return "audio_silent_0000"

        # FFT spectral energy in 8 frequency bands
        fft = np.abs(np.fft.rfft(audio_pcm))
        bands = np.array_split(fft, 8)
        band_energies = [int(np.log1p(np.mean(b)) * 10) for b in bands]
        return "-".join(f"{e:02x}" for e in band_energies)

    def extract_dna(
        self,
        media_bytes: Optional[bytes] = None,
        key_frame_bgr: Optional[np.ndarray] = None,
        audio_pcm: Optional[np.ndarray] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> MediaDNA:
        """Synthesizes complete Media DNA profile."""
        meta = metadata or {}
        
        sha = self.compute_sha256(media_bytes) if media_bytes else hashlib.sha256(b"live_session").hexdigest()
        p_hash = self.compute_perceptual_hash(key_frame_bgr) if key_frame_bgr is not None else "0000000000000000"
        a_fp = self.compute_audio_fingerprint(audio_pcm) if audio_pcm is not None else None
        
        res = f"{key_frame_bgr.shape[1]}x{key_frame_bgr.shape[0]}" if key_frame_bgr is not None else meta.get("resolution", "1280x720")

        return MediaDNA(
            media_sha256=sha,
            perceptual_hash=p_hash,
            audio_fingerprint=a_fp,
            temporal_fingerprint=f"cadence_{meta.get('fps', 30.0):.1f}fps",
            codec_metadata=meta,
            duration_seconds=float(meta.get("duration", 0.0)),
            resolution=res,
            frame_rate=float(meta.get("fps', 5.0")),
        )
