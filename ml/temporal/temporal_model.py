"""
Temporal Consistency Analysis using PyTorch rolling GRU sequence model.
Monitors feature sequence stability, facial jitter, warping, and temporal discontinuities.
"""
import os
from collections import deque
from typing import List, Optional
import numpy as np
import torch
import torch.nn as nn

from backend.app.config import settings, get_active_device
from backend.app.schemas.contracts import TemporalResult


class TemporalGRU(nn.Module):
    def __init__(self, input_dim: int = 1280, hidden_dim: int = 64):
        super().__init__()
        self.gru = nn.GRU(input_size=input_dim, hidden_size=hidden_dim, batch_first=True)
        self.classifier = nn.Sequential(
            nn.Linear(hidden_dim, 32),
            nn.ReLU(),
            nn.Linear(32, 1),
            nn.Sigmoid(),
        )

    def forward(self, x):
        # x: (batch, seq_len, input_dim)
        _, h_n = self.gru(x)
        out = self.classifier(h_n.squeeze(0))
        return out


class TemporalAnalyzer:
    def __init__(self, window_size: int = 16, feature_dim: int = 1280, device: Optional[str] = None):
        self.window_size = window_size
        self.feature_dim = feature_dim
        self.device_name = device or get_active_device()
        self.device = torch.device(self.device_name)
        
        self.model = TemporalGRU(input_dim=feature_dim).to(self.device)

        # Check for fine-tuned weights
        chk_path = os.path.join(os.path.dirname(__file__), "../checkpoints/fine_tuned_temporal_gru.pt")
        if os.path.exists(chk_path):
            try:
                chk = torch.load(chk_path, map_location=self.device)
                self.model.load_state_dict(chk["state_dict"])
            except Exception:
                pass

        self.model.eval()
        
        # Rolling buffer of feature vectors
        self.feature_buffer: deque = deque(maxlen=window_size)
        self.bbox_buffer: deque = deque(maxlen=window_size)

    def push_frame_features(
        self, feature_vector: np.ndarray, bbox: Optional[List[int]] = None
    ) -> TemporalResult:
        """
        Ingests next frame feature vector and updates rolling temporal sequence.
        Returns TemporalResult.
        """
        if feature_vector is None or len(feature_vector) == 0:
            return TemporalResult(
                temporal_anomaly_score=0.0,
                feature_variance=0.0,
                continuity_break=False,
                status="NO_DATA",
            )

        # Normalize feature vector
        norm = np.linalg.norm(feature_vector)
        feat_norm = feature_vector / (norm + 1e-7)
        self.feature_buffer.append(feat_norm)

        if bbox is not None:
            self.bbox_buffer.append(bbox)

        # If buffer not filled yet, status is BUFFERING (neutral baseline)
        if len(self.feature_buffer) < 8:
            return TemporalResult(
                temporal_anomaly_score=0.06,
                feature_variance=0.0,
                continuity_break=False,
                status="BUFFERING",
            )

        # Check for bbox continuity break (teleporting face / sudden jitter)
        continuity_break = False
        if len(self.bbox_buffer) >= 2:
            prev_b = self.bbox_buffer[-2]
            curr_b = self.bbox_buffer[-1]
            # Center distance relative to face size
            prev_center = (prev_b[0] + prev_b[2] / 2, prev_b[1] + prev_b[3] / 2)
            curr_center = (curr_b[0] + curr_b[2] / 2, curr_b[1] + curr_b[3] / 2)
            dist = np.hypot(curr_center[0] - prev_center[0], curr_center[1] - prev_center[1])
            if dist > max(curr_b[2], curr_b[3]) * 1.8:
                continuity_break = True

        # Frame-to-frame cosine similarity variance
        buf_list = list(self.feature_buffer)
        sims = []
        for i in range(len(buf_list) - 1):
            cos_sim = float(np.dot(buf_list[i], buf_list[i+1]))
            sims.append(cos_sim)
        
        sim_variance = float(np.var(sims)) if sims else 0.0

        # Run through PyTorch GRU model
        seq_tensor = torch.tensor(
            np.array(buf_list), dtype=torch.float32, device=self.device
        ).unsqueeze(0)
        
        with torch.no_grad():
            raw_score = self.model(seq_tensor).item()

        # Natural speaking and head posture shifts exhibit slight variance (<= 0.08).
        # We only escalate the score for abnormal synthetic warping or face flickering.
        calibrated_model_score = max(0.04, min(1.0, (raw_score - 0.40) * 1.6)) if raw_score > 0.40 else 0.06
        abnormal_jitter = max(0.0, sim_variance - 0.08) * 2.0
        score = calibrated_model_score * 0.5 + min(1.0, abnormal_jitter) * 0.5
        if continuity_break:
            score = min(1.0, score + 0.3)

        return TemporalResult(
            temporal_anomaly_score=round(float(score), 4),
            feature_variance=round(sim_variance, 4),
            continuity_break=continuity_break,
            status="OK",
        )
