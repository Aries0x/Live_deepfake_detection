"""
Audio-Video Synchronization Module.
Correlates mouth landmark dynamics (lip opening/closing distance) with acoustic speech energy.

SCORE SEMANTICS:
- av_sync_score: 1.0 = synchronized speech, 0.0 = completely out-of-sync / mismatched.
- contradiction_score: (1.0 - av_sync_score) used by fusion engine as anomaly indicator.
"""
from collections import deque
from typing import List, Optional
import numpy as np
from scipy.signal import correlate

from backend.app.schemas.contracts import SyncResult


class AVSyncAnalyzer:
    def __init__(self, window_seconds: float = 2.0, video_fps: int = 5, audio_sr: int = 16000):
        self.video_fps = video_fps
        self.audio_sr = audio_sr
        self.max_video_frames = int(window_seconds * video_fps)
        
        self.mouth_motion_history: deque = deque(maxlen=self.max_video_frames)
        self.audio_energy_history: deque = deque(maxlen=self.max_video_frames)

    def extract_mouth_opening(self, landmarks: Optional[List[List[float]]]) -> float:
        """
        Extracts vertical mouth opening distance normalized by face size.
        landmarks: [[x_eye1, y], [x_eye2, y], [x_nose, y], [x_mouth_l, y], [x_mouth_r, y]]
        """
        if not landmarks or len(landmarks) < 5:
            return 0.0

        # Normalized lip width & motion proxy
        mouth_l = np.array(landmarks[3])
        mouth_r = np.array(landmarks[4])
        width = np.linalg.norm(mouth_r - mouth_l)
        
        # Vertical distance from nose to mouth plane
        nose = np.array(landmarks[2])
        mouth_center = (mouth_l + mouth_r) / 2.0
        vert_dist = float(mouth_center[1] - nose[1])
        
        normalized_opening = vert_dist / (width + 1e-6)
        return float(normalized_opening)

    def update(
        self,
        landmarks: Optional[List[List[float]]],
        audio_chunk: Optional[np.ndarray],
    ) -> SyncResult:
        """
        Process simultaneous video frame landmarks and audio energy chunk.
        """
        # Calculate mouth motion
        opening = self.extract_mouth_opening(landmarks)
        self.mouth_motion_history.append(opening)

        # Calculate audio chunk energy
        if audio_chunk is not None and len(audio_chunk) > 0:
            audio_rms = float(np.sqrt(np.mean(audio_chunk**2)))
        else:
            audio_rms = 0.0
        self.audio_energy_history.append(audio_rms)

        # Need sufficient frames to compute cross-correlation
        if len(self.mouth_motion_history) < 6:
            return SyncResult(
                av_sync_score=0.85,
                contradiction_score=0.15,
                mouth_motion_energy=opening,
                audio_energy=audio_rms,
                offset_ms=0.0,
                status="BUFFERING",
            )

        mouth_sig = np.array(self.mouth_motion_history)
        audio_sig = np.array(self.audio_energy_history)

        # Normalize signals
        mouth_norm = mouth_sig - np.mean(mouth_sig)
        audio_norm = audio_sig - np.mean(audio_sig)
        
        mouth_std = np.std(mouth_norm)
        audio_std = np.std(audio_norm)

        # If silence or motionless face, synchronization is inconclusive / normal
        if mouth_std < 1e-4 or audio_std < 1e-4:
            return SyncResult(
                av_sync_score=0.90,
                contradiction_score=0.10,
                mouth_motion_energy=round(float(mouth_std), 4),
                audio_energy=round(float(audio_std), 4),
                offset_ms=0.0,
                status="INACTIVE_SPEECH",
            )

        # Cross-correlation between mouth motion and audio energy
        mouth_norm /= mouth_std
        audio_norm /= audio_std

        corr = correlate(mouth_norm, audio_norm, mode='full')
        corr /= len(mouth_norm)
        
        max_idx = np.argmax(corr)
        max_corr = float(corr[max_idx])
        
        lag_frames = max_idx - (len(mouth_norm) - 1)
        lag_ms = (lag_frames / self.video_fps) * 1000.0

        # Normal speaking lag is within +/- 150ms
        lag_penalty = max(0.0, (abs(lag_ms) - 150.0) / 300.0)
        
        # Raw sync bounded [0, 1]
        raw_sync = max(0.0, min(1.0, (max_corr + 1.0) / 2.0))
        final_sync_score = max(0.0, raw_sync - lag_penalty * 0.4)
        contradiction = 1.0 - final_sync_score

        return SyncResult(
            av_sync_score=round(float(final_sync_score), 4),
            contradiction_score=round(float(contradiction), 4),
            mouth_motion_energy=round(float(mouth_std), 4),
            audio_energy=round(float(audio_std), 4),
            offset_ms=round(float(lag_ms), 1),
            status="OK",
        )
