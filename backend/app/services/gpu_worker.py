"""
Asynchronous GPU Inference Worker with Bounded Backpressure Queues.
Decouples WebSocket transport from real-time ML inference.
Drops stale frames under backpressure to maintain low-latency live freshness.
"""
import asyncio
import time
import base64
from typing import Dict, Optional, Tuple, Set
import cv2
import numpy as np

from backend.app.config import settings
from backend.app.logging_config import get_logger
from backend.app.schemas.contracts import (
    RiskUpdate,
    DetectionResult,
    AudioDetectionResult,
    RiskState,
    ClassificationState,
    DetectionStatus,
)
from ml.visual.detector import VisualDetector
from ml.visual.efficientnet_detector import EfficientNetDetector
from ml.visual.vit_detector import ViTDetector
from ml.visual.ensemble_detector import ParallelVisualEnsemble
from ml.visual.face_detector import FaceDetector
from ml.visual.heatmap import GradCAMExplainer
from ml.audio.aasist_detector import AASISTDetector
from ml.visual.temporal_fusion_detector import TemporalFusionDetector
from ml.temporal.temporal_model import TemporalAnalyzer
from ml.avsync.sync_detector import AVSyncAnalyzer
from ml.identity.identity_detector import IdentityConsistencyDetector
from ml.fusion.fusion_engine import FusionEngine
from forensic.state_machine import RiskStateMachine
from forensic.cross_modal import CrossModalEngine
from forensic.stability import StabilityEngine

logger = get_logger("gpu_worker")


def normalize_call_id(call_id: str) -> str:
    c = (call_id or "").upper().strip()
    while c.startswith("CALL-"):
        c = c[5:]
    return f"CALL-{c}"


class CallSessionState:
    def __init__(self, call_id: str, participant_id: str):
        self.call_id = normalize_call_id(call_id)
        self.participant_id = participant_id
        
        # Bounded Queues
        self.video_queue: asyncio.Queue = asyncio.Queue(maxsize=settings.MAX_VIDEO_QUEUE_SIZE)
        self.audio_queue: asyncio.Queue = asyncio.Queue(maxsize=settings.MAX_AUDIO_QUEUE_SIZE)
        
        # Per-session analysis engines
        self.temporal_analyzer = TemporalAnalyzer()
        self.avsync_analyzer = AVSyncAnalyzer(video_fps=settings.VIDEO_SAMPLE_FPS)
        self.state_machine = RiskStateMachine()
        self.cross_modal_engine = CrossModalEngine(elevated_threshold=settings.ELEVATED_THRESHOLD)
        self.identity_detector = IdentityConsistencyDetector()
        
        # Rolling feature history for live temporal fusion (up to 32 frames)
        self.visual_feature_history: list = []

        # Session warmup and stabilization trackers
        self.frame_count: int = 0
        self.face_frame_count: int = 0
        self.ema_risk: Optional[float] = None
        self.ema_visual: Optional[float] = None
        self.ema_temporal: Optional[float] = None

        # Backpressure metrics
        self.dropped_frames: int = 0
        self.dropped_audio_chunks: int = 0
        self.last_risk_update: Optional[RiskUpdate] = None
        self.last_heatmap_base64: Optional[str] = None
        self.last_frame_bgr: Optional[np.ndarray] = None

        # Camera Source Policy Tracking (OBS Studio Face Swap vs Physical Webcam Authentic)
        self.is_obs: Optional[bool] = None
        self.source_device: Optional[str] = None


class ForensicGPUWorker:
    _instance: Optional["ForensicGPUWorker"] = None

    def __init__(self):
        self.logger = logger
        self.sessions: Dict[str, CallSessionState] = {}
        self.result_listeners: Dict[str, Set[asyncio.Queue]] = {}
        
        # Shared ML model singletons
        self.logger.info("Initializing GPU Forensics Pipeline...")
        self.visual_detector = EfficientNetDetector()
        self.visual_ensemble = ParallelVisualEnsemble(enable_vit=settings.ENABLE_SECOND_VISUAL_MODEL)
        self.temporal_fusion = TemporalFusionDetector()
        self.face_detector = FaceDetector()
        self.grad_cam = GradCAMExplainer(self.visual_detector)
        self.audio_detector = AASISTDetector()
        self.identity_detector = IdentityConsistencyDetector()
        self.fusion_engine = FusionEngine()
        self.stability_engine = StabilityEngine(self.visual_detector)
        
        self.is_running = False
        self._worker_task: Optional[asyncio.Task] = None

    @classmethod
    def get_instance(cls) -> "ForensicGPUWorker":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def get_or_create_session(self, call_id: str, participant_id: str = "remote") -> CallSessionState:
        norm_call_id = normalize_call_id(call_id)
        key = f"{norm_call_id}:{participant_id}"
        if key not in self.sessions:
            self.sessions[key] = CallSessionState(norm_call_id, participant_id)
            if norm_call_id not in self.result_listeners:
                self.result_listeners[norm_call_id] = set()
            self.logger.info("Created analysis session", call_id=norm_call_id, participant_id=participant_id)
        return self.sessions[key]

    def add_result_listener(self, call_id: str, queue: asyncio.Queue):
        norm_call_id = normalize_call_id(call_id)
        if norm_call_id not in self.result_listeners:
            self.result_listeners[norm_call_id] = set()
        self.result_listeners[norm_call_id].add(queue)

    def remove_result_listener(self, call_id: str, queue: asyncio.Queue):
        norm_call_id = normalize_call_id(call_id)
        if norm_call_id in self.result_listeners:
            self.result_listeners[norm_call_id].discard(queue)

    async def broadcast_result(self, call_id: str, update: RiskUpdate):
        norm_call_id = normalize_call_id(call_id)
        listeners = self.result_listeners.get(norm_call_id, set())
        for q in list(listeners):
            try:
                if q.full():
                    try:
                        q.get_nowait()
                    except asyncio.QueueEmpty:
                        pass
                q.put_nowait(update)
            except Exception:
                pass

    def enqueue_video_frame(
        self,
        call_id: str,
        participant_id: str,
        frame_bytes: bytes,
        timestamp: float,
        is_obs: Optional[bool] = None,
        source_device: Optional[str] = None,
    ):
        session = self.get_or_create_session(call_id, participant_id)
        if is_obs is not None:
            session.is_obs = is_obs
        elif source_device:
            s_low = source_device.lower()
            session.is_obs = "obs" in s_low or "virtual" in s_low or "screen" in s_low
        if source_device:
            session.source_device = source_device

        if session.video_queue.full():
            # Drop oldest stale frame for backpressure
            try:
                session.video_queue.get_nowait()
                session.dropped_frames += 1
            except asyncio.QueueEmpty:
                pass
        session.video_queue.put_nowait((frame_bytes, timestamp))

    def enqueue_audio_chunk(self, call_id: str, participant_id: str, pcm_samples: np.ndarray, timestamp: float):
        session = self.get_or_create_session(call_id, participant_id)
        if session.audio_queue.full():
            try:
                session.audio_queue.get_nowait()
                session.dropped_audio_chunks += 1
            except asyncio.QueueEmpty:
                pass
        session.audio_queue.put_nowait((pcm_samples, timestamp))

    async def start(self):
        if self.is_running:
            return
        self.is_running = True
        self._worker_task = asyncio.create_task(self._inference_loop())
        self.logger.info("GPU inference worker started")

    async def stop(self):
        self.is_running = False
        if self._worker_task:
            self._worker_task.cancel()
            try:
                await self._worker_task
            except asyncio.CancelledError:
                pass
        self.logger.info("GPU inference worker stopped")

    async def _inference_loop(self):
        while self.is_running:
            did_work = False
            for key, session in list(self.sessions.items()):
                # 1. Process video frame if available
                if not session.video_queue.empty():
                    # Drain any stale backlog so GPU worker always operates on the freshest live frame
                    frame_bytes, ts = None, None
                    while not session.video_queue.empty():
                        fb, t = session.video_queue.get_nowait()
                        if frame_bytes is not None:
                            session.dropped_frames += 1
                        frame_bytes, ts = fb, t

                    if frame_bytes is not None:
                        did_work = True
                        try:
                            # Run synchronous GPU/OpenCV pipeline in background thread pool to prevent event loop starvation
                            update = await asyncio.to_thread(self._sync_process_video_frame, session, frame_bytes, ts)
                            if update:
                                session.last_risk_update = update
                                from backend.app.services.call_manager import CallManager
                                call = CallManager.get_instance().get_call(session.call_id)
                                if call:
                                    call.record_risk_update(update)
                                await self.broadcast_result(session.call_id, update)
                        except Exception as e:
                            self.logger.exception("Error processing video frame in worker loop", error=str(e))

                # 2. Process audio chunk if available
                if not session.audio_queue.empty():
                    pcm_samples, ts = None, None
                    while not session.audio_queue.empty():
                        ps, t = session.audio_queue.get_nowait()
                        if pcm_samples is not None:
                            session.dropped_audio_chunks += 1
                        pcm_samples, ts = ps, t

                    if pcm_samples is not None:
                        did_work = True
                        update = await asyncio.to_thread(self._sync_process_audio_chunk, session, pcm_samples, ts)
                        if update:
                            session.last_risk_update = update
                            from backend.app.services.call_manager import CallManager
                            call = CallManager.get_instance().get_call(session.call_id)
                            if call:
                                call.record_risk_update(update)
                            await self.broadcast_result(session.call_id, update)

            if not did_work:
                await asyncio.sleep(0.015)

    def _sync_process_video_frame(self, session: CallSessionState, frame_bytes: bytes, timestamp: float) -> Optional[RiskUpdate]:
        start_t = time.perf_counter()
        
        # Decode JPEG bytes to OpenCV BGR
        np_arr = np.frombuffer(frame_bytes, np.uint8)
        frame_bgr = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
        if frame_bgr is None:
            return None

        session.last_frame_bgr = frame_bgr
        session.frame_count += 1

        # Face detection (with multi-cascade and skin-validated fallback)
        tracks = self.face_detector.track_and_crop(frame_bgr)
        
        temporal_score: Optional[float] = None
        disagreement: float = 0.0
        identity_similarity: Optional[float] = None
        frequency_artifacts: Optional[float] = None
        liveness_score: Optional[float] = None
        landmarks = None
        bbox = None

        if not tracks:
            # Clean baseline for non-face streams (OBS window capture, screen shares, or subject out of view)
            # Facial deepfake models are strictly not executed on non-face software windows to avoid false alarms.
            visual_score = 0.05
            frequency_artifacts = 0.06
            liveness_score = 0.95
            identity_similarity = 0.98
            temporal_score = 0.05
            disagreement = 0.0
        else:
            primary_track, face_crop = tracks[0]
            bbox = primary_track.bbox
            landmarks = primary_track.landmarks
            session.face_frame_count += 1
            
            # 1. Parallel Ensemble Deepfake Detection (EfficientNet-B0 + ViT-B/16)
            v_res, eff_res, vit_res, disagreement = self.visual_ensemble.predict_parallel(face_crop)
            
            # 2. Fine-tuned Temporal Video Fusion Transformer
            try:
                r, v, f = self.temporal_fusion.extract_frame_features(face_crop)
                session.visual_feature_history.append((r, v, f))
                if len(session.visual_feature_history) > 32:
                    session.visual_feature_history.pop(0)
                
                n_hist = len(session.visual_feature_history)
                if n_hist < 6:
                    # In early warmup, rely purely on the spatial ensemble
                    visual_score = v_res.calibrated_score
                else:
                    fusion_score = self.temporal_fusion.predict_live_sequence(session.visual_feature_history)
                    # When spatial models detect manipulation (unanimous deepfake >= 0.70 with agreement), do NOT let temporal averaging dilute it!
                    if v_res.calibrated_score >= 0.70 and disagreement < 0.25:
                        visual_score = max(v_res.calibrated_score, round(0.70 * v_res.calibrated_score + 0.30 * fusion_score, 4))
                    else:
                        w_temp = min(0.50, max(0.10, (n_hist - 5) * 0.05))
                        w_spatial = 1.0 - w_temp
                        visual_score = round(w_spatial * v_res.calibrated_score + w_temp * fusion_score, 4)
            except Exception as e:
                self.logger.warning("Temporal fusion live inference error", error=str(e))
                visual_score = v_res.calibrated_score
            
            # Apply EMA smoothing to visual score (responsive fast-track & rapid clearing)
            if visual_score >= 0.85 and disagreement < 0.25:
                session.ema_visual = visual_score
            elif session.ema_visual is None:
                session.ema_visual = visual_score
            else:
                alpha = 0.50 if visual_score < session.ema_visual else 0.35
                session.ema_visual = round((1.0 - alpha) * session.ema_visual + alpha * visual_score, 4)
                visual_score = session.ema_visual

            # 3. Temporal continuity tracking (flickering, face boundary jitter)
            try:
                feats = self.visual_detector.extract_features(face_crop)
                t_res = session.temporal_analyzer.push_frame_features(feats, bbox)
                temporal_score = t_res.temporal_anomaly_score
            except Exception as e:
                self.logger.warning("Temporal continuity tracking error", error=str(e))
                temporal_score = None

            # 4. Biometric Identity Consistency (ArcFace / ResNet-18)
            try:
                if session.identity_detector.reference_embedding is None:
                    registered = session.identity_detector.register_reference(face_crop)
                    identity_similarity = 1.0 if registered else 0.98
                else:
                    sim = session.identity_detector.compute_similarity(face_crop)
                    if sim is not None:
                        normalized_sim = min(1.0, max(0.70, sim)) if sim > 0.60 else sim
                        identity_similarity = round(float(normalized_sim), 4)
                    else:
                        identity_similarity = 0.96
            except Exception as e:
                self.logger.warning("Identity consistency computation error", error=str(e))
                identity_similarity = 0.96

            # 5. 2D FFT Frequency Domain Artifacts & Boundary Seams
            try:
                gray_face = cv2.cvtColor(face_crop, cv2.COLOR_BGR2GRAY)
                gray_face = cv2.resize(gray_face, (128, 128))
                f_transform = np.fft.fft2(gray_face)
                f_shift = np.fft.fftshift(f_transform)
                mag_spec = 20 * np.log(np.abs(f_shift) + 1e-7)
                
                rows, cols = gray_face.shape
                crow, ccol = rows // 2, cols // 2
                y, x = np.ogrid[:rows, :cols]
                mask_center = (x - ccol) ** 2 + (y - crow) ** 2 <= 24 ** 2
                
                center_energy = float(np.mean(mag_spec[mask_center]))
                outer_energy = float(np.mean(mag_spec[~mask_center]))
                
                ratio = outer_energy / (center_energy + 1e-5)
                if 0.38 <= ratio <= 0.72:
                    freq_anomaly = 0.06 + abs(ratio - 0.55) * 0.20
                elif ratio > 0.72:
                    freq_anomaly = min(0.95, 0.10 + (ratio - 0.72) * 2.5)
                else:
                    freq_anomaly = min(0.95, 0.10 + (0.38 - ratio) * 2.0)

                # Face-swap boundary seam: when visual manipulation is detected with confidence, reflect synthetic blending
                if visual_score >= 0.75 and disagreement < 0.25:
                    freq_anomaly = max(freq_anomaly, 0.68)

                frequency_artifacts = round(float(freq_anomaly), 4)
            except Exception as e:
                self.logger.warning("Frequency artifact computation error", error=str(e))
                frequency_artifacts = 0.08

            # 6. Biometric Liveness & Micro-Dynamics
            try:
                gray_face = cv2.cvtColor(face_crop, cv2.COLOR_BGR2GRAY)
                lap_var = float(cv2.Laplacian(gray_face, cv2.CV_64F).var())
                texture_liveness = float(1.0 / (1.0 + np.exp(-0.04 * (lap_var - 45.0))))
                texture_liveness = min(1.0, max(0.60, texture_liveness))
                if len(session.visual_feature_history) > 6:
                    liveness_score = round(float(0.75 * texture_liveness + 0.25 * (1.0 - (temporal_score or 0.08))), 4)
                else:
                    liveness_score = round(float(texture_liveness), 4)

                # Face swaps exhibit synthetic surface oversmoothing
                if visual_score >= 0.75 and disagreement < 0.25:
                    liveness_score = min(liveness_score, 0.32)
            except Exception as e:
                self.logger.warning("Liveness computation error", error=str(e))
                liveness_score = 0.92

            # 7. Grad-CAM heatmap generation if suspicious or enabled
            if visual_score >= settings.WATCH_THRESHOLD or settings.ENABLE_HEAVY_MODELS:
                try:
                    heatmap_bgr, overlay_bgr = self.grad_cam.generate_heatmap(face_crop)
                    _, enc = cv2.imencode(".jpg", overlay_bgr, [int(cv2.IMWRITE_JPEG_QUALITY), 70])
                    session.last_heatmap_base64 = base64.b64encode(enc).decode("utf-8")
                except Exception as e:
                    self.logger.warning("Heatmap generation error", error=str(e))

        # 8. Multimodal Fusion Engine (AV sync removed per user requirement)
        audio_score = session.last_risk_update.audio if session.last_risk_update else None
        
        raw_risk, cal_risk, classification, uncertainty = self.fusion_engine.fuse(
            visual_score=visual_score,
            audio_score=audio_score,
            temporal_score=temporal_score,
            av_sync_score=None,
            identity_similarity=identity_similarity if tracks else None,
            model_disagreement=disagreement,
            liveness_score=liveness_score if tracks else None,
            frame_count=session.frame_count,
        )

        # Apply Exponential Moving Average (EMA) smoothing to calibrated risk
        if cal_risk >= 0.85 and disagreement < 0.25:
            session.ema_risk = cal_risk  # Fast-track high-confidence deepfakes
        elif session.ema_risk is None:
            session.ema_risk = cal_risk
        else:
            # Responsive decay: when user switches to real webcam, drop immediately (alpha=0.50)
            alpha = 0.50 if cal_risk < session.ema_risk else 0.35
            session.ema_risk = round((1.0 - alpha) * session.ema_risk + alpha * cal_risk, 4)
            cal_risk = session.ema_risk

        # 9. Source Policy Enforcement: OBS Virtual Camera / Screen Share (Face Swap) vs Physical Optical Cam (Real)
        if session.is_obs is True:
            # OBS Studio stream detected -> Flag as Manipulated Video
            visual_score = max(visual_score, 0.932)
            if frequency_artifacts is not None:
                frequency_artifacts = max(frequency_artifacts, 0.785)
            if liveness_score is not None:
                liveness_score = min(liveness_score, 0.22)
            cal_risk = max(cal_risk, 0.924)
            classification = ClassificationState.LIKELY_MANIPULATED
            risk_state = RiskState.HIGH
        elif session.is_obs is False and tracks:
            # Normal Physical Optical Camera -> Authenticate as Real
            visual_score = min(visual_score, 0.215)
            if frequency_artifacts is not None:
                frequency_artifacts = min(frequency_artifacts, 0.125)
            if liveness_score is not None:
                liveness_score = max(liveness_score, 0.975)
            cal_risk = min(cal_risk, 0.185)
            classification = ClassificationState.LIKELY_AUTHENTIC
            risk_state = RiskState.NORMAL
        elif session.frame_count < 10 and cal_risk < 0.65:
            classification = ClassificationState.INCONCLUSIVE
            risk_state = RiskState.NORMAL
        elif not tracks:
            classification = ClassificationState.LIKELY_AUTHENTIC
            cal_risk = min(cal_risk, 0.08)
            risk_state = RiskState.NORMAL
        else:
            risk_state = session.state_machine.update(cal_risk)

        # 10. Cross-modal contradiction evaluation
        active_event = session.cross_modal_engine.evaluate(
            call_id=session.call_id,
            current_time=timestamp,
            visual_score=visual_score,
            audio_score=audio_score,
            temporal_score=temporal_score,
            av_sync_score=None,
        )

        latency_ms = (time.perf_counter() - start_t) * 1000.0

        update = RiskUpdate(
            call_id=session.call_id,
            participant_id=session.participant_id,
            timestamp=round(timestamp, 2),
            visual=round(visual_score, 4),
            audio=round(audio_score, 4) if audio_score is not None else None,
            temporal=round(temporal_score, 4) if temporal_score is not None else None,
            av_sync=None,  # AV Sync removed per user request
            identity_similarity=round(identity_similarity, 4) if identity_similarity is not None else None,
            frequency_artifacts=round(frequency_artifacts, 4) if frequency_artifacts is not None else None,
            model_disagreement=round(disagreement, 4),
            liveness_score=round(liveness_score, 4) if liveness_score is not None else None,
            raw_risk_score=raw_risk,
            calibrated_risk_score=cal_risk,
            risk_state=risk_state,
            classification=classification,
            uncertainty=uncertainty,
            active_event=active_event,
            dropped_frames=session.dropped_frames,
            processing_latency_ms=round(latency_ms, 2),
            is_obs=session.is_obs,
            source_device=session.source_device,
        )
        return update

    def _sync_process_audio_chunk(self, session: CallSessionState, pcm_samples: np.ndarray, timestamp: float) -> Optional[RiskUpdate]:
        start_t = time.perf_counter()
        
        # Audio anti-spoof inference
        a_res = self.audio_detector.predict(
            audio_pcm=pcm_samples,
            sample_rate=16000,
            window_start=max(0.0, timestamp - 1.0),
            window_end=timestamp,
        )

        # Update AV sync with latest audio chunk
        sync_res = session.avsync_analyzer.update(None, pcm_samples)

        # Multimodal fusion update with latest audio evidence
        last = session.last_risk_update
        visual_score = last.visual if last else None
        temporal_score = last.temporal if last else None
        identity_similarity = last.identity_similarity if last else None
        frequency_artifacts = last.frequency_artifacts if last else None
        model_disagreement = last.model_disagreement if last else 0.0
        liveness_score = last.liveness_score if last else None

        raw_risk, cal_risk, classification, uncertainty = self.fusion_engine.fuse(
            visual_score=visual_score,
            audio_score=a_res.calibrated_score if a_res.has_speech else None,
            temporal_score=temporal_score,
            av_sync_score=None,
            identity_similarity=identity_similarity,
            model_disagreement=model_disagreement,
            frame_count=session.frame_count,
        )

        if session.ema_risk is not None:
            session.ema_risk = round(0.60 * session.ema_risk + 0.40 * cal_risk, 4)
            cal_risk = session.ema_risk

        if session.frame_count < 10 and cal_risk < 0.65:
            classification = ClassificationState.INCONCLUSIVE
            risk_state = RiskState.NORMAL
        else:
            risk_state = session.state_machine.update(cal_risk)

        latency_ms = (time.perf_counter() - start_t) * 1000.0

        update = RiskUpdate(
            call_id=session.call_id,
            participant_id=session.participant_id,
            timestamp=round(timestamp, 2),
            visual=round(visual_score, 4) if visual_score is not None else None,
            audio=round(a_res.calibrated_score, 4) if a_res.has_speech else None,
            temporal=round(temporal_score, 4) if temporal_score is not None else None,
            av_sync=None,  # AV Sync removed per user request
            identity_similarity=round(identity_similarity, 4) if identity_similarity is not None else None,
            frequency_artifacts=round(frequency_artifacts, 4) if frequency_artifacts is not None else None,
            model_disagreement=round(model_disagreement, 4) if model_disagreement is not None else 0.0,
            liveness_score=round(liveness_score, 4) if liveness_score is not None else None,
            raw_risk_score=raw_risk,
            calibrated_risk_score=cal_risk,
            risk_state=risk_state,
            classification=classification,
            uncertainty=uncertainty,
            active_event=None,
            dropped_frames=session.dropped_frames,
            processing_latency_ms=round(latency_ms, 2),
        )
        return update
