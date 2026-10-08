# Architecture — Media Integrity / SecureCall

## System Overview

SecureCall is a real-time multimodal media forensics platform built on the principle:

**DETECT → CORRELATE → LOCALIZE → STRESS-TEST → EXPLAIN → AUDIT**

## High-Level Architecture

```
                         ┌───────────────────┐
                         │     USER CALL     │
                         └─────────┬─────────┘
                                   │
                                WebRTC
                                   │
                    ┌──────────────┴──────────────┐
                    │                             │
                    ▼                             ▼
                 VIDEO                          AUDIO
                    │                             │
               5 FPS sample                  1-sec windows
                    │                             │
                    ▼                             ▼
              SCRFD-500M                      VAD
                    │                             │
                    ▼                             ▼
              Face alignment                 AASIST-L
                    │                             │
                    ▼                             ▼
               Face crop                    Voice score
                    │
          ┌─────────┼──────────┐
          ▼         ▼          ▼
     EfficientNet  ArcFace   Landmarks
          │         │          │
          ▼         ▼          ▼
       Visual     Identity   Mouth motion
       score      score          │
          │         │            ▼
          │         │         SyncNet
          │         │            │
          └─────────┼────────────┘
                    ▼
             Temporal model (GRU)
                    │
                    ▼
          Cross-modal engine
                    │
                    ▼
             Evidence fusion
                    │
                    ▼
         Calibration / uncertainty
                    │
                    ▼
           Evidence stability
                    │
                    ▼
          Continuous risk engine
                    │
        ┌───────────┼────────────┐
        ▼           ▼            ▼
      Heatmap    Timeline    Evidence graph
        │           │            │
        └───────────┼────────────┘
                    ▼
             Forensic report
                    │
                    ▼
               Audit chain
                    │
                    ▼
                PostgreSQL
```

## Technology Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js, React, TypeScript, Tailwind CSS, WebRTC, WebSocket, Recharts |
| Backend | Python 3.11+, FastAPI, Pydantic, WebSockets |
| ML | PyTorch, torchvision, torchaudio, OpenCV, NumPy, SciPy, librosa |
| Database | PostgreSQL |
| Cache/Queue | Redis |
| Media | FFmpeg, FFprobe |
| Containers | Docker, Docker Compose |
| Testing | Pytest, Playwright |

## Module Structure

### Frontend (`frontend/`)
- Next.js application with TypeScript
- Pages: Landing, Call, Dashboard, Cases, Bulk, Reports, Settings
- WebRTC peer connection management
- WebSocket client for analysis data transport
- Real-time risk visualization with Recharts

### Backend (`backend/`)
- FastAPI application
- REST API endpoints (`/api/v1/...`)
- WebSocket endpoints for real-time analysis
- GPU worker with bounded queues
- Database models and migrations
- Report generation

### ML (`ml/`)
- `ml/visual/` — Face detection (SCRFD), deepfake detection (EfficientNet), heatmaps (Grad-CAM)
- `ml/audio/` — Voice activity detection, anti-spoofing (AASIST-L)
- `ml/temporal/` — Temporal consistency analysis (GRU)
- `ml/avsync/` — Audio-video synchronization (SyncNet-style)
- `ml/identity/` — Face identity embedding (ArcFace)
- `ml/fusion/` — Evidence fusion engine

### Forensic (`forensic/`)
- Cross-modal contradiction detection
- Evidence stability engine
- Media DNA fingerprinting
- C2PA/provenance inspection
- Report generation

### Audit (`audit/`)
- Tamper-evident hash chain
- Event logging
- Chain verification

## Data Flow

### Live Call Analysis
1. Browser captures remote video/audio via WebRTC
2. Video: Canvas sampling at ~5 FPS → JPEG → WebSocket → Backend
3. Audio: AudioWorklet → PCM chunks → WebSocket → Backend
4. Backend queues frames/audio in bounded queues
5. GPU worker processes: face detection → crop → visual model → score
6. Audio worker processes: VAD → windowing → audio model → score
7. Temporal model analyzes feature sequences
8. A/V sync model compares mouth motion to audio
9. Cross-modal engine detects contradictions
10. Fusion engine combines all evidence
11. Risk state machine updates continuously
12. Results pushed to frontend via WebSocket

### Bulk Verification
1. Upload ZIP / multiple files via REST API
2. Validate, hash, create job
3. Process each file through full pipeline
4. Generate CSV/JSON summary

## Risk State Machine

```
NORMAL → WATCH → ELEVATED → HIGH
  ↑        ↑        ↑         │
  └────────┴────────┴─────────┘
         (recovery)
```

- Transitions require temporal persistence (not single-frame triggers)
- Configurable thresholds: `MIN_SUSPICIOUS_WINDOWS`, `MIN_MULTIMODAL_AGREEMENT`
- Recovery requires sustained absence of evidence

## Security Architecture

- All uploads: MIME validation, size limits, randomized storage names
- FFmpeg: subprocess with argument arrays only
- WebSocket: session-based authentication
- Audit log: tamper-evident SHA-256 hash chain
- Media hashing: SHA-256 of actual bytes (never filename-only)
- No secrets in logs

## Deployment

- Docker Compose for local development
- Services: frontend, backend, postgres, redis
- GPU passthrough via NVIDIA Container Toolkit
- Environment-based configuration via `.env`
