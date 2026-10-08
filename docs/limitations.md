# Limitations — Media Integrity / SecureCall

## Core Limitations

This system provides **automated forensic evidence and decision support**. It does **not** guarantee authenticity.

### Detection Limitations

The system may fail on:
- **Unseen generators** — Novel deepfake methods not represented in training data
- **Heavy compression** — Extreme JPEG/video compression destroys manipulation artifacts
- **Low-quality media** — Low resolution, poor lighting, or heavy noise reduce accuracy
- **Novel attacks** — Adversarial manipulations specifically designed to evade detection
- **Unusual lighting** — Extreme lighting conditions affect face detection and analysis
- **Severe occlusion** — Faces partially hidden by objects, hands, or masks
- **Adversarial manipulation** — Inputs specifically crafted to fool the detector

### Model Limitations

- Models are trained on specific datasets and may not generalize to all scenarios
- EfficientNet-based detectors may not detect manipulation methods not in training data
- Audio anti-spoofing models may miss novel voice synthesis techniques
- Temporal analysis depends on sufficient frame count (minimum ~16 frames)
- A/V sync analysis requires both visible mouth movement and audible speech

### System Limitations

- Real-time analysis at ~5 FPS — some manipulations may be missed between samples
- GPU required for real-time performance — CPU mode is significantly slower
- WebRTC quality depends on network conditions
- Browser must support WebRTC, Web Audio API, and modern JavaScript features
- PostgreSQL and Redis required for full functionality

### Calibration Limitations

- Raw model scores are NOT calibrated probabilities
- Score thresholds are configurable but require tuning for specific use cases
- False positive and false negative rates depend on threshold configuration
- Model disagreement does not necessarily indicate uncertainty

### Evidence Stability Limitations

- Stability testing adds latency — only triggered for ELEVATED/HIGH events
- Controlled transformations may not cover all real-world distortions
- High stability does not guarantee correctness of the original detection

## Disclaimers

> This report is an automated forensic assessment based on the analyzed media and configured models. It should be treated as decision support and may contain false positives or false negatives.

> Attribution visualization (heatmaps) shows regions that contributed to the model prediction; it is not independent proof of manipulation.

> Identity mismatch is evidence, not proof — it may result from pose, occlusion, lighting, resolution, or tracking errors.
