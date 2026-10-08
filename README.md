# SecureCall / Media Integrity Platform

[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688.svg?logo=fastapi)](https://fastapi.tiangolo.com)
[![Next.js](https://img.shields.io/badge/Frontend-Next.js%2014-black.svg?logo=next.js)](https://nextjs.org)
[![PyTorch](https://img.shields.io/badge/ML-PyTorch%202.x-EE4C2C.svg?logo=pytorch)](https://pytorch.org)
[![TypeScript](https://img.shields.io/badge/Code-TypeScript-blue.svg?logo=typescript)](https://www.typescriptlang.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/Tests-Passing-brightgreen.svg)]()

**Real-Time Multimodal Media Forensics, Live WebRTC Deepfake Detection, and Tamper-Evident Judicial Verification Platform.**

SecureCall continuously monitors and evaluates live audio and video streams during peer-to-peer communications to detect synthetic facial manipulation, voice cloning, audio-video desynchronization, and identity tampering in real time.

---

## Table of Contents

- [Core Principles](#core-principles)
- [Key Innovations](#key-innovations)
- [System Architecture](#system-architecture)
- [Multimodal Detection Engines](#multimodal-detection-engines)
- [Explainable AI (XAI) Forensic Synthesis](#explainable-ai-xai-forensic-synthesis)
- [Tamper-Evident Audit & Judicial Chain of Custody](#tamper-evident-audit--judicial-chain-of-custody)
- [Role-Based Access Control (RBAC)](#role-based-access-control-rbac)
- [Quick Start](#quick-start)
  - [Prerequisites](#prerequisites)
  - [Backend Setup](#backend-setup)
  - [Frontend Setup](#frontend-setup)
  - [Docker Setup](#docker-setup)
- [Running Test Suites](#running-test-suites)
- [Repository Structure](#repository-structure)
- [Documentation Index](#documentation-index)
- [License & Responsible Use](#license--responsible-use)

---

## Core Principles

```
DETECT → CORRELATE → LOCALIZE → STRESS-TEST → EXPLAIN → AUDIT
```

The system treats model outputs as **probabilistic evidence, never absolute ground truth**. It enforces strictly calibrated, evidentiary classifications:
- **`LIKELY AUTHENTIC`**: Multimodal cues align with genuine human physiology and acoustic physics.
- **`INCONCLUSIVE`**: Insufficient sensor confidence, low resolution, or partial occlusions prevent definitive assessment.
- **`LIKELY MANIPULATED`**: Multiple independent models detect synthetic artifacts, frequency anomalies, or cross-modal contradictions.

---

## Key Innovations

1. **Continuous Trust Trajectory**:
   Instead of one-off frame checks, SecureCall maintains an adaptive temporal state machine that tracks trust confidence over the entire duration of a live call.
2. **Cross-Modal Contradiction Detection**:
   Evaluates joint agreement between facial dynamics and vocal acoustics, catching desynchronization, lip-audio latency, and conflicting modality risk.
3. **Evidence Stability Stress-Testing**:
   Suspicious frames are perturbed with controlled compression, Gaussian noise, and blur transformations to differentiate authentic compression noise from genuine deepfake artifacts.
4. **Perceptual Media DNA**:
   Combines cryptographic frame hashes with perceptual feature representations to ensure forensic provenance and tamper detection.
5. **Tamper-Evident SHA-256 Audit Trail**:
   Every forensic decision, metric update, and state transition is committed to an append-only, cryptographic hash-chained audit ledger.
6. **Explainable AI (XAI) Judicial Dossiers**:
   Synthesizes granular model metrics into courtroom-ready forensic summaries grounded strictly in measurable empirical evidence.

---

## System Architecture

```
User (WebRTC Call) ──► Peer Video & Audio Stream
                           │
       ┌───────────────────┴───────────────────┐
       ▼                                       ▼
  [Video Pipeline]                        [Audio Pipeline]
   - SCRFD Face Detection                  - Voice Activity Detection (VAD)
   - EfficientNet-B0 Visual Artifacts      - AASIST-L Anti-Spoofing (GAT)
   - Spatial Grad-CAM Localization         - Linear Frequency Cepstral Analysis
   - FFT High-Frequency Residuals          - Phase & Spectral Cutoff Check
       │                                       │
       └───────────────────┬───────────────────┘
                           ▼
                  [Cross-Modal Correlation]
                   - Audio-Visual SyncNet (Lip Latency)
                   - Temporal Consistency (GRU Window)
                   - Identity Verification (ArcFace)
                           │
                           ▼
                  [Evidence Fusion Engine]
                   - Calibrated Probabilistic Fusion
                   - Stability Stress-Test Engine
                           │
                           ▼
                [Continuous State Machine]
                 LOW_RISK ◄► ELEVATED ◄► HIGH_RISK
                           │
        ┌──────────────────┴──────────────────┐
        ▼                                     ▼
[Live Forensic Dashboard]            [Forensic Audit & Reports]
 - Real-Time Risk Gauges              - SHA-256 Hash Chaining
 - Heatmaps & Attention Overlays     - Downloadable Judicial PDF/HTML Dossiers
 - Anomaly Timeline & Audio Spectrogram - Supabase Cloud Storage Sync
```

---

## Multimodal Detection Engines

| Subsystem | Model / Technology | Primary Detection Objective |
| :--- | :--- | :--- |
| **Face Localization** | SCRFD (InsightFace) | Fast, robust face bounding-box & 5-point landmark detection. |
| **Visual Manipulation** | EfficientNet-B0 + ViT-B/16 | Seam boundaries, blending artifacts, and GAN/diffusion synthesis traces. |
| **Audio Anti-Spoofing** | AASIST-L (Graph Attention) | Synthetic voice generation, neural vocoder signatures, spectral cutoffs. |
| **A/V Synchronization** | SyncNet (Cross-Correlation) | Lip motion vs. acoustic energy latency & desynchronization. |
| **Temporal Dynamics** | Bi-Directional GRU | Inconsistent inter-frame transitions, unnatural blinking, head flutter. |
| **Identity Continuity** | ArcFace Embeddings | Identity drift and face-swap substitution during live streams. |
| **Evidence Fusion** | Calibrated Multi-Modal Fusion | Unified risk probability combining weighted modality confidence. |

---

## Explainable AI (XAI) Forensic Synthesis

SecureCall features a dedicated Explainable AI engine capable of translating raw forensic scores (Grad-CAM attention points, FFT residuals, spectral cutoffs, SyncNet latency) into courtroom-defensible prose:
- Cross-correlates visual manipulation hotspots with acoustic vocoder traces.
- Validates findings against evidence stability scores.
- Adheres to zero-hallucination evidentiary standards for legal admissibility.

---

## Tamper-Evident Audit & Judicial Chain of Custody

All inspection events are chained using cryptographic SHA-256 links:
```
Block(N) = SHA-256( Block(N-1).hash + Event_Type + Timestamp + Metrics_Digest + Nonce )
```
Any retroactive modification of logs, scores, or forensic reports invalidates the cryptographic chain, providing indisputable integrity verification in judicial proceedings.

---

## Role-Based Access Control (RBAC)

The platform enforces strict role separation for civil, institutional, and judicial workflows:
- **Citizen / Public**: Live call integrity, one-time verification, and privacy-preserving ephemeral storage.
- **Forensic Officer**: Full diagnostic metric access, bulk video verification, Grad-CAM overlays, and 2FA authentication.
- **Judge / Court**: Immutable case reviews, tamper-evident hash validation, and certified judicial PDF dossiers.
- **Administrator**: User provisioning, model registry configuration, and system telemetry.

---

## Quick Start

### Prerequisites
- **Python 3.11+**
- **Node.js 18+** & **npm**
- **FFmpeg** (installed and available on PATH)
- **NVIDIA GPU with CUDA** *(optional — full CPU fallback is supported)*

### Backend Setup

1. **Create and activate a virtual environment**:
   ```bash
   python -m venv .venv
   # Windows PowerShell:
   .\.venv\Scripts\Activate.ps1
   # Linux / macOS:
   source .venv/bin/activate
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt  # Or pip install fastapi uvicorn torch opencv-python pydantic-settings
   ```

3. **Configure environment variables**:
   ```bash
   cp .env.example .env
   # Edit .env with your specific settings (default SQLite works out-of-the-box)
   ```

4. **Launch the backend server**:
   ```bash
   uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
   ```

### Frontend Setup

1. **Navigate to the frontend directory**:
   ```bash
   cd frontend
   ```

2. **Install dependencies**:
   ```bash
   npm install
   ```

3. **Configure frontend environment**:
   ```bash
   cp .env.local.example .env.local
   ```

4. **Run the development server**:
   ```bash
   npm run dev
   ```
   Open [http://localhost:3000](http://localhost:3000) in your browser.

### Docker Setup

Run the entire platform (FastAPI, Redis, PostgreSQL, Next.js) with Docker Compose:
```bash
docker-compose up --build
```

---

## Running Test Suites

SecureCall includes automated unit, integration, and security test suites:

```bash
# Run unit tests (forensics, fusion, audit chain, stability)
pytest tests/test_unit_forensics.py -v

# Run integration tests (FastAPI endpoints, call lifecycles, bulk processing)
pytest tests/test_integration_api.py -v

# Run full test suite
pytest tests/ -v
```

---

## Repository Structure

```
.
├── backend/              # FastAPI application & microservices
│   ├── app/
│   │   ├── api/          # REST & WebSocket route handlers (calls, bulk, metrics)
│   │   ├── services/     # Supabase sync, storage, audio/video analysis services
│   │   ├── websocket/    # Live WebRTC stream packet ingestors
│   │   └── config.py     # Environment and settings configuration
│   └── auth/             # Role-based access control, TOTP 2FA, JWT handling
├── ml/                   # Multimodal machine learning engines
│   ├── visual/           # Face detection, EfficientNet-B0, ViT Grad-CAM
│   ├── audio/            # AASIST-L voice anti-spoofing & VAD
│   ├── temporal/         # Bi-directional GRU temporal consistency
│   ├── avsync/           # SyncNet audio-video cross-correlation
│   ├── identity/         # ArcFace facial biometric verification
│   └── fusion/           # Calibrated evidence fusion engine
├── forensic/             # Forensic verification subsystems
│   ├── cross_modal.py    # Visual vs. acoustic correlation engine
│   ├── stability.py      # Perturbation & noise stress-testing
│   ├── media_dna.py      # Cryptographic & perceptual media fingerprinting
│   ├── explainable_ai.py # Multi-modal reasoning & XAI synthesis
│   └── c2pa.py           # Content Authenticity Initiative / C2PA inspector
├── frontend/             # Next.js 14 App Router client application
│   ├── app/              # Routes: /call (Live WebRTC), /bulk (Batch verification)
│   ├── components/       # Heatmaps, risk meters, timelines, waveform charts
│   └── lib/              # API clients, WebSocket adapters, authentication
├── audit/                # Cryptographic audit logging & SHA-256 hash chaining
├── reports/              # HTML & PDF forensic dossier generation
├── tests/                # Automated pytest test suites (unit, integration, e2e)
├── scripts/              # Evaluation benchmarks and startup automation scripts
├── docs/                 # Exhaustive technical documentation & architecture guides
└── docker-compose.yml    # Production container orchestration
```

---

## Documentation Index

- [Architecture & Data Flow](docs/architecture.md)
- [System Technical Specifications](docs/system-specifications.md)
- [Model Registry & Benchmark Accuracy](docs/model-registry.md)
- [Datasets & Split Methodology](docs/datasets.md)
- [Security Architecture & Threat Model](docs/security.md)
- [Privacy & Ephemeral Retention Standards](docs/privacy.md)
- [Component & Open Source Licenses](docs/licenses.md)
- [Live Demonstration Guide](docs/demo-guide.md)
- [System Limitations & Boundary Conditions](docs/limitations.md)

---

## License & Responsible Use

This software is released under the [MIT License](LICENSE).

**Ethical & Responsible Use Disclosure**:
SecureCall is engineered strictly as a defensive media forensic verification technology. It is designed to safeguard individuals, organizations, and legal institutions against synthetic fraud, impersonation attacks, and unauthorized voice cloning. It does not provide tools for media generation or synthetic deception.
