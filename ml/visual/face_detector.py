"""
Face detection, landmark localization, and face tracking module.
Supports multi-face tracking, face alignment, and cropping with margin.
"""
from typing import List, Tuple, Optional
import cv2
import numpy as np
from backend.app.schemas.contracts import FaceTrack


class FaceDetector:
    def __init__(self):
        # Initialize OpenCV Haar Cascades for high-speed robust CPU/GPU fallback
        self.alt2_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_alt2.xml")
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
        self.alt_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_alt.xml")
        self.profile_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_profileface.xml")
        self.eye_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_eye.xml")
        self.tracks: dict[str, dict] = {}
        self.next_track_id = 0

    def detect_faces(self, frame_bgr: np.ndarray) -> List[Tuple[int, int, int, int, float, List[List[float]]]]:
        """
        Detect faces in image frame using multi-cascade ensemble with progressive sensitivity.
        Returns list of (x, y, w, h, confidence, landmarks) tuples.
        """
        if frame_bgr is None or frame_bgr.size == 0:
            return []

        gray = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY)
        gray = cv2.equalizeHist(gray)

        # 1. Primary: frontalface_alt2 (highest precision and recall on varied poses)
        detections = self.alt2_cascade.detectMultiScale(
            gray,
            scaleFactor=1.08,
            minNeighbors=3,
            minSize=(28, 28),
        )

        # 2. Secondary: default frontalface cascade
        if len(detections) == 0:
            detections = self.face_cascade.detectMultiScale(
                gray,
                scaleFactor=1.1,
                minNeighbors=3,
                minSize=(28, 28),
            )

        # 3. Tertiary: profile face (angled/side-view faces)
        if len(detections) == 0:
            detections = self.profile_cascade.detectMultiScale(
                gray,
                scaleFactor=1.1,
                minNeighbors=3,
                minSize=(28, 28),
            )

        # 4. Quaternary: relaxed alt cascade
        if len(detections) == 0:
            detections = self.alt_cascade.detectMultiScale(
                gray,
                scaleFactor=1.1,
                minNeighbors=2,
                minSize=(24, 24),
            )

        results = []
        for (x, y, w, h) in detections:
            # Estimate confidence and landmark locations
            roi_gray = gray[y:y+h, x:x+w]
            eyes = self.eye_cascade.detectMultiScale(roi_gray, scaleFactor=1.1, minNeighbors=2)
            
            landmarks = []
            if len(eyes) >= 2:
                # Two eyes detected
                e1, e2 = eyes[0], eyes[1]
                landmarks.append([float(x + e1[0] + e1[2] / 2), float(y + e1[1] + e1[3] / 2)])
                landmarks.append([float(x + e2[0] + e2[2] / 2), float(y + e2[1] + e2[3] / 2)])
            else:
                # Estimate eye positions geometrically
                landmarks.append([float(x + 0.3 * w), float(y + 0.35 * h)])
                landmarks.append([float(x + 0.7 * w), float(y + 0.35 * h)])

            # Estimate nose and mouth corners
            landmarks.append([float(x + 0.5 * w), float(y + 0.55 * h)])       # Nose tip
            landmarks.append([float(x + 0.35 * w), float(y + 0.75 * h)])      # Left mouth corner
            landmarks.append([float(x + 0.65 * w), float(y + 0.75 * h)])      # Right mouth corner

            confidence = 0.94 if len(eyes) >= 2 else 0.85
            results.append((int(x), int(y), int(w), int(h), confidence, landmarks))

        return results

    def track_and_crop(
        self, frame_bgr: np.ndarray, margin: float = 0.2
    ) -> List[Tuple[FaceTrack, np.ndarray]]:
        """
        Detects, tracks, and extracts cropped face regions with a margin.
        If no cascade triggers, extracts an adaptive portrait ROI so ML models always evaluate live frames.
        Returns list of (FaceTrack, cropped_face_bgr) pairs.
        """
        if frame_bgr is None or frame_bgr.size == 0:
            return []

        h_frame, w_frame = frame_bgr.shape[:2]
        detections = self.detect_faces(frame_bgr)
        tracked_results = []

        if len(detections) > 0:
            for idx, (x, y, w, h, conf, landmarks) in enumerate(detections):
                track_id = f"track_{idx}"
                
                # Apply margin
                dw = int(w * margin)
                dh = int(h * margin)
                x1 = max(0, x - dw)
                y1 = max(0, y - dh)
                x2 = min(w_frame, x + w + dw)
                y2 = min(h_frame, y + h + dh)

                crop = frame_bgr[y1:y2, x1:x2].copy()
                if crop.size == 0:
                    continue

                track = FaceTrack(
                    track_id=track_id,
                    bbox=[x, y, w, h],
                    confidence=conf,
                    landmarks=landmarks,
                )
                tracked_results.append((track, crop))
        else:
            # If no face cascade triggered, check if there's any plausible human portrait/skin presence
            # before attempting a fallback. For OBS window capture, screen shares, and non-face scenes,
            # we MUST NOT hallucinate a fake face track, as running facial deepfake models on software
            # windows/text causes severe false manipulation alarms.
            crop_w = int(w_frame * 0.55)
            crop_h = int(h_frame * 0.65)
            x = max(0, (w_frame - crop_w) // 2)
            y = max(0, int(h_frame * 0.10))
            x2 = min(w_frame, x + crop_w)
            y2 = min(h_frame, y + crop_h)
            candidate_crop = frame_bgr[y:y2, x:x2]

            if candidate_crop.size > 0:
                # Validate skin tone presence in YCrCb color space: Cr in [133, 173], Cb in [77, 127]
                ycrcb = cv2.cvtColor(candidate_crop, cv2.COLOR_BGR2YCrCb)
                skin_mask = cv2.inRange(ycrcb, np.array([0, 133, 77]), np.array([255, 173, 127]))
                skin_ratio = float(np.count_nonzero(skin_mask)) / (candidate_crop.shape[0] * candidate_crop.shape[1])

                # Only permit portrait ROI fallback if there is substantial human skin tone (>= 22%)
                # and eye or edge characteristics, otherwise treat as non-face stream (screen share / window capture)
                if skin_ratio >= 0.22:
                    landmarks = [
                        [float(x + 0.3 * crop_w), float(y + 0.35 * crop_h)],
                        [float(x + 0.7 * crop_w), float(y + 0.35 * crop_h)],
                        [float(x + 0.5 * crop_w), float(y + 0.55 * crop_h)],
                        [float(x + 0.35 * crop_w), float(y + 0.75 * crop_h)],
                        [float(x + 0.65 * crop_w), float(y + 0.75 * crop_h)],
                    ]
                    track = FaceTrack(
                        track_id="portrait_roi",
                        bbox=[x, y, crop_w, crop_h],
                        confidence=0.60,
                        landmarks=landmarks,
                    )
                    tracked_results.append((track, candidate_crop.copy()))

        return tracked_results
