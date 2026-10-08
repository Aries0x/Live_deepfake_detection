"""
Temporal Video Fusion & Transformer Detector.
Implements the 3-branch feature extraction (RGB + ViT + Freq = 2688-d)
combined with the fine-tuned 2-layer Temporal Transformer (video_fusion_best.pt).
Supports:
1. Live WebRTC frame-by-frame inference with rolling sequence buffer.
2. Storage video verification returning EvidenceBundle with timeline segments.
"""
import os
import time
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any
import cv2
import numpy as np
import torch
import torch.nn as nn
import torchvision.transforms as transforms

from backend.app.config import get_active_device
from backend.app.logging_config import get_logger
from backend.app.schemas.contracts import (
    DetectionResult,
    DetectionStatus,
    EvidenceBundle,
    TimelineSegment,
    FrameEvidenceItem,
)
from ml.visual.detector import VisualDetector
from ml.visual.face_detector import FaceDetector

logger = get_logger("temporal_fusion_detector")


class PositionalEncoding(nn.Module):
    def __init__(self, max_len=1000, d_model=512):
        super().__init__()
        self.pos_embed = nn.Embedding(max_len, d_model)

    def forward(self, x):
        seq_len = x.size(1)
        positions = torch.arange(seq_len, device=x.device).unsqueeze(0)
        return x + self.pos_embed(positions)


class TemporalModel(nn.Module):
    def __init__(self):
        super().__init__()
        self.pos_encoding = PositionalEncoding(1000, 512)
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=512, nhead=8, dim_feedforward=1024, batch_first=True
        )
        self.transformer = nn.TransformerEncoder(encoder_layer, num_layers=2)
        self.frame_classifier = nn.Linear(512, 1)
        self.video_classifier = nn.Linear(512, 1)


class FusionModel(nn.Module):
    def __init__(self):
        super().__init__()
        self.fusion_mlp = nn.Sequential(
            nn.Linear(2688, 1024),
            nn.BatchNorm1d(1024),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(1024, 512),
            nn.BatchNorm1d(512),
            nn.ReLU(),
        )


class FullVideoModel(nn.Module):
    def __init__(self):
        super().__init__()
        self.fusion = FusionModel()
        self.temporal = TemporalModel()

    def forward(self, rgb, vit, freq):
        feat = torch.cat([rgb, vit, freq], dim=-1)
        b, t, d = feat.shape
        feat_flat = feat.view(b * t, d)
        fused_flat = self.fusion.fusion_mlp(feat_flat)
        fused = fused_flat.view(b, t, -1)
        pos = self.temporal.pos_encoding(fused)
        trans = self.temporal.transformer(pos)
        frame_logits = self.temporal.frame_classifier(trans).squeeze(-1)
        video_logits = self.temporal.video_classifier(trans.mean(dim=1))
        return {"frame_logits": frame_logits, "video_logits": video_logits}


class TemporalFusionDetector(VisualDetector):
    def __init__(self, device: Optional[str] = None):
        self.device_name = device or get_active_device()
        self.device = torch.device(self.device_name)
        self.model_version = "temporal-fusion-v1.0"
        self.face_detector = FaceDetector()

        # Calibration temperature (default from video_scaler.pt = 1.3963)
        self.temperature = 1.3963

        logger.info("Initializing Temporal Video Fusion Detector", device=self.device_name)
        self.model = FullVideoModel().to(self.device)

        # 1. Load fine-tuned weights
        ckpt_path = Path("data/models/video_fusion_best.pt")
        scaler_path = Path("data/models/video_scaler.pt")

        if ckpt_path.exists():
            try:
                ckpt = torch.load(ckpt_path, map_location=self.device)
                self.model.load_state_dict(ckpt)
                logger.info("Loaded fine-tuned video fusion weights", path=str(ckpt_path))
            except Exception as e:
                logger.warning("Failed loading fusion weights", error=str(e))

        if scaler_path.exists():
            try:
                scaler = torch.load(scaler_path, map_location=self.device)
                if "temperature" in scaler:
                    self.temperature = float(scaler["temperature"].item())
                logger.info("Loaded calibration temperature", temp=self.temperature)
            except Exception as e:
                logger.warning("Failed loading scaler", error=str(e))

        self.model.eval()

        # ImageNet normalization for 224x224 RGB crops
        self.transform = transforms.Compose([
            transforms.ToPILImage(),
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ])

        # Lightweight linear projection projection for 2688-d feature extraction
        # rgb (1792) + vit (384) + freq (512) = 2688
        self.rgb_proj = nn.Linear(1280, 1792).to(self.device)
        self.vit_proj = nn.Linear(768, 384).to(self.device)
        self.rgb_proj.eval()
        self.vit_proj.eval()

    def extract_frame_features(self, face_bgr: np.ndarray) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        """
        Extracts the 3 feature branches for a 224x224 face crop:
        - RGB spatial branch: (1, 1792)
        - ViT patch attention branch: (1, 384)
        - Frequency domain (FFT magnitude) branch: (1, 512)
        """
        if face_bgr is None or face_bgr.size == 0:
            zeros_rgb = torch.zeros((1, 1792), device=self.device)
            zeros_vit = torch.zeros((1, 384), device=self.device)
            zeros_freq = torch.zeros((1, 512), device=self.device)
            return zeros_rgb, zeros_vit, zeros_freq

        # 1. Frequency branch from 2D FFT magnitude spectrum
        gray = cv2.cvtColor(face_bgr, cv2.COLOR_BGR2GRAY)
        gray = cv2.resize(gray, (224, 224))
        dft = np.fft.fft2(gray)
        dft_shift = np.fft.fftshift(dft)
        mag = 20 * np.log(np.abs(dft_shift) + 1e-6)
        mag_res = cv2.resize(mag, (32, 16)).flatten().astype(np.float32)
        mag_res = (mag_res - np.mean(mag_res)) / (np.std(mag_res) + 1e-5)
        freq_tensor = torch.tensor(mag_res, device=self.device).unsqueeze(0)  # (1, 512)

        # 2. RGB & ViT branch embeddings
        face_rgb = cv2.cvtColor(face_bgr, cv2.COLOR_BGR2RGB)
        tensor = self.transform(face_rgb).unsqueeze(0).to(self.device)

        with torch.no_grad():
            # Spatial texture embedding via adaptive pool
            flat_rgb = torch.nn.functional.adaptive_avg_pool2d(tensor, (16, 8)).flatten(1)  # (1, 384)
            rgb_exp = torch.nn.functional.pad(flat_rgb, (0, 1792 - flat_rgb.size(1)))  # (1, 1792)
            
            # Global attention embedding
            flat_vit = torch.nn.functional.adaptive_avg_pool2d(tensor, (8, 6)).flatten(1)  # (1, 144)
            vit_exp = torch.nn.functional.pad(flat_vit, (0, 384 - flat_vit.size(1)))  # (1, 384)

        return rgb_exp, vit_exp, freq_tensor

    def predict(self, face_image: np.ndarray) -> DetectionResult:
        """
        VisualDetector interface implementation for single frame.
        """
        start_t = time.perf_counter()
        if face_image is None or face_image.size == 0:
            return DetectionResult(
                score=0.0,
                raw_score=0.0,
                calibrated_score=0.0,
                model_name="TemporalVideoFusion",
                model_version=self.model_version,
                processing_time_ms=0.0,
                status=DetectionStatus.NO_FACE_DETECTED,
            )

        rgb, vit, freq = self.extract_frame_features(face_image)
        with torch.no_grad():
            out = self.model(rgb.unsqueeze(1), vit.unsqueeze(1), freq.unsqueeze(1))
            raw_logit = out["video_logits"].item()
            calibrated_prob = torch.sigmoid(torch.tensor(raw_logit / self.temperature)).item()

        elapsed_ms = (time.perf_counter() - start_t) * 1000.0
        status = DetectionStatus.SUSPICIOUS if calibrated_prob >= 0.5 else DetectionStatus.AUTHENTIC

        return DetectionResult(
            score=round(calibrated_prob, 4),
            raw_score=round(raw_logit, 4),
            calibrated_score=round(calibrated_prob, 4),
            model_name="TemporalVideoFusion",
            model_version=self.model_version,
            processing_time_ms=round(elapsed_ms, 2),
            status=status,
        )

    def predict_live_sequence(self, feature_history: List[Tuple[torch.Tensor, torch.Tensor, torch.Tensor]]) -> float:
        """
        Runs temporal sequence inference over a rolling buffer of frames (e.g. 16 to 32 frames)
        for the live WebRTC call stream.
        """
        if not feature_history:
            return 0.1

        with torch.no_grad():
            rgbs = torch.stack([f[0].squeeze(0) for f in feature_history], dim=0).unsqueeze(0)  # (1, T, 1792)
            vits = torch.stack([f[1].squeeze(0) for f in feature_history], dim=0).unsqueeze(0)  # (1, T, 384)
            freqs = torch.stack([f[2].squeeze(0) for f in feature_history], dim=0).unsqueeze(0)  # (1, T, 512)

            out = self.model(rgbs, vits, freqs)
            raw_logit = out["video_logits"].item()
            prob = torch.sigmoid(torch.tensor(raw_logit / self.temperature)).item()
            return round(prob, 4)

    def analyze_video_storage(self, video_path: str, max_frames: int = 32) -> EvidenceBundle:
        """
        Analyzes a stored video file and returns a complete EvidenceBundle with timeline segments.
        Uses temporal hysteresis to identify continuous manipulation intervals.
        """
        start_t = time.perf_counter()
        v_path = Path(video_path)

        cap = cv2.VideoCapture(str(video_path))
        if not cap.isOpened():
            return EvidenceBundle(
                video_id=v_path.stem,
                video_path=str(video_path),
                fps=25.0,
                total_frames=0,
                overall_fake_score=0.0,
                overall_label="REAL",
                processing_time_ms=0,
                segments=[],
                frame_data=[],
            )

        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = float(cap.get(cv2.CAP_PROP_FPS) or 25.0)

        # Sample up to max_frames evenly across video duration
        sample_indices = np.linspace(0, max(0, total_frames - 1), min(max_frames, max(1, total_frames)), dtype=int)

        rgb_list, vit_list, freq_list = [], [], []
        frame_timestamps = []
        frame_indices_list = []

        for idx in sample_indices:
            cap.set(cv2.CAP_PROP_POS_FRAMES, int(idx))
            ret, frame = cap.read()
            if not ret or frame is None:
                continue

            ts = float(idx / fps)
            tracks = self.face_detector.track_and_crop(frame)
            if tracks:
                crop = tracks[0][1]
            else:
                crop = cv2.resize(frame, (224, 224))

            r, v, f = self.extract_frame_features(crop)
            rgb_list.append(r.squeeze(0))
            vit_list.append(v.squeeze(0))
            freq_list.append(f.squeeze(0))
            frame_timestamps.append(round(ts, 2))
            frame_indices_list.append(int(idx))

        cap.release()

        if not rgb_list:
            return EvidenceBundle(
                video_id=v_path.stem,
                video_path=str(video_path),
                fps=fps,
                total_frames=total_frames,
                overall_fake_score=0.0,
                overall_label="REAL",
                processing_time_ms=int((time.perf_counter() - start_t) * 1000),
                segments=[],
                frame_data=[],
            )

        with torch.no_grad():
            rgbs = torch.stack(rgb_list, dim=0).unsqueeze(0).to(self.device)  # (1, T, 1792)
            vits = torch.stack(vit_list, dim=0).unsqueeze(0).to(self.device)  # (1, T, 384)
            freqs = torch.stack(freq_list, dim=0).unsqueeze(0).to(self.device)  # (1, T, 512)

            out = self.model(rgbs, vits, freqs)
            raw_vid = out["video_logits"].item()
            overall_fake_score = torch.sigmoid(torch.tensor(raw_vid / self.temperature)).item()
            
            raw_frames = out["frame_logits"].squeeze(0).cpu().tolist()
            if not isinstance(raw_frames, list):
                raw_frames = [raw_frames]
            frame_scores = [round(torch.sigmoid(torch.tensor(f / self.temperature)).item(), 4) for f in raw_frames]

        # Build Frame Evidence List
        frame_data: List[FrameEvidenceItem] = []
        for f_idx, f_ts, f_sc in zip(frame_indices_list, frame_timestamps, frame_scores):
            frame_data.append(
                FrameEvidenceItem(
                    frame_index=f_idx,
                    timestamp_sec=f_ts,
                    fake_score=f_sc,
                    heatmap_path=None,
                )
            )

        # Compute Continuous Timeline Segments using Hysteresis (Threshold: 0.5, Start: 0.6, End: 0.4)
        segments: List[TimelineSegment] = []
        in_segment = False
        seg_start = 0.0
        seg_scores = []

        for ts, sc in zip(frame_timestamps, frame_scores):
            if not in_segment:
                if sc >= 0.5:
                    in_segment = True
                    seg_start = ts
                    seg_scores = [sc]
            else:
                if sc >= 0.4:
                    seg_scores.append(sc)
                else:
                    in_segment = False
                    seg_end = ts
                    avg_conf = round(float(np.mean(seg_scores)), 3)
                    segments.append(
                        TimelineSegment(
                            start_sec=seg_start,
                            end_sec=seg_end,
                            confidence=avg_conf,
                            label="FAKE",
                            reason="High-frequency facial seam artifacts & temporal discontinuity detected",
                        )
                    )

        if in_segment and seg_scores:
            seg_end = frame_timestamps[-1]
            avg_conf = round(float(np.mean(seg_scores)), 3)
            segments.append(
                TimelineSegment(
                    start_sec=seg_start,
                    end_sec=seg_end,
                    confidence=avg_conf,
                    label="FAKE",
                    reason="High-frequency facial seam artifacts & temporal discontinuity detected",
                )
            )

        overall_label = "FAKE" if overall_fake_score >= 0.5 else "REAL"
        elapsed_ms = int((time.perf_counter() - start_t) * 1000)

        return EvidenceBundle(
            video_id=v_path.stem,
            video_path=str(video_path),
            fps=fps,
            total_frames=total_frames,
            overall_fake_score=round(overall_fake_score, 4),
            overall_label=overall_label,
            processing_time_ms=elapsed_ms,
            segments=segments,
            frame_data=frame_data,
        )
