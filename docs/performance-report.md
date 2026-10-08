# Performance Report — Media Integrity / SecureCall

> **Note:** All values in this document must be measured on actual hardware. Do not invent benchmark numbers.

## Target Hardware

- **GPU:** NVIDIA RTX 5050
- **Device:** Configured via `DEVICE` environment variable

## Measured Latencies

| Stage | Measured (ms) | Device | Notes |
|-------|--------------|--------|-------|
| Face detection (SCRFD) | TBD | TBD | Pending model installation |
| Visual inference (EfficientNet-B0) | TBD | TBD | Pending model installation |
| Visual inference (EfficientNet-B4) | TBD | TBD | Pending model installation |
| Audio inference (AASIST-L) | TBD | TBD | Pending model installation |
| Temporal analysis (GRU) | TBD | TBD | Pending model training |
| A/V sync (SyncNet) | TBD | TBD | Pending model installation |
| Fusion | TBD | TBD | |
| Heatmap (Grad-CAM) | TBD | TBD | Pending model installation |
| End-to-end alert | TBD | TBD | |

## Resource Usage

| Metric | Measured | Notes |
|--------|----------|-------|
| GPU VRAM usage | TBD | |
| GPU utilization (%) | TBD | |
| CPU usage (%) | TBD | |
| RAM usage (MB) | TBD | |
| Analysis FPS | TBD | Target: ~5 FPS |
| Dropped frames (%) | TBD | |

## Processing Health Dashboard

```
Video inference:  TBD ms
Audio inference:  TBD ms
End-to-end:       TBD ms
Dropped frames:   TBD
GPU VRAM:         TBD
```

## CPU Fallback Performance

| Stage | CPU (ms) | Notes |
|-------|----------|-------|
| Face detection | TBD | Expected significantly slower |
| Visual inference | TBD | |
| Audio inference | TBD | |

---

*This document will be updated with actual measurements after model installation and testing.*
