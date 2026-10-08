# MASTER BUILD PROMPT
## Real-Time Multimodal Media Forensics and Live Call Verification Platform

You are the lead software architect, ML engineer, backend engineer, frontend engineer, MLOps engineer, security engineer, and QA engineer for this project.

Your job is to build a complete, runnable, modular prototype from an empty repository.

Do **not** produce only a demo UI.
Do **not** produce only an ML notebook.
Do **not** create fake inference results.
Do **not** claim a model works unless it has actually been loaded and executed.

Build the full pipeline end-to-end, make every subsystem independently testable, and verify the running application through automated tests and browser testing.

The final system must support:

1. A live two-person WebRTC call.
2. Real-time analysis of the remote participant's video.
3. Real-time analysis of the remote participant's audio.
4. Face manipulation detection.
5. Synthetic/voice-spoof detection.
6. Temporal consistency analysis.
7. Audio-video synchronization analysis.
8. Identity consistency as an optional signal.
9. Multimodal evidence fusion.
10. Continuous risk assessment during the call.
11. Suspicious-event timeline.
12. Visual attribution/heatmap generation.
13. Evidence stability testing.
14. Media fingerprint / Media DNA generation.
15. C2PA/provenance inspection where applicable.
16. Tamper-evident forensic audit logging.
17. A forensic report.
18. Bulk offline media verification.
19. A controlled synthetic-media attack demo using consenting teammates.
20. Clear uncertainty handling and an INCONCLUSIVE state.

This is a defensive media-integrity/security application.

Use only authorized, consent-based synthetic-media test inputs.

Do not implement mechanisms intended to bypass real-world biometric systems or defeat third-party security controls.

---

# 1. PRODUCT DEFINITION

Product name:

**Media Integrity / SecureCall**

Primary purpose:

Continuously assess whether the media presented during a live communication contains evidence of synthetic generation, manipulation, replay, identity inconsistency, or audio-video inconsistency.

The product must **not** make absolute claims such as:

- `100% real`
- `100% fake`

Instead, use:

- `LIKELY AUTHENTIC`
- `INCONCLUSIVE`
- `LIKELY MANIPULATED`

and separately expose evidence and uncertainty.

The system should treat every model output as evidence, not truth.

---

# 2. CORE PRODUCT CONCEPT

The product is based on:

**DETECT → CORRELATE → LOCALIZE → STRESS-TEST → EXPLAIN → AUDIT**

Core architecture:

```text
User
  ↓
WebRTC Call
  ↓
Remote Audio + Remote Video
  ↓
┌─────────────────────────────────────┐
│ Real-Time Media Processing Layer    │
└─────────────────────────────────────┘
  ↓
┌─────────────────┬───────────────────┐
│                 │                   │
VIDEO             AUDIO               CONTEXT
│                 │                   │
↓                 ↓                   ↓
Face detection    Voice activity      Metadata
↓                 ↓                   ↓
Face crop         Audio windows       Provenance
↓                 ↓
Visual model      Audio anti-spoof model
↓                 ↓
Visual score      Audio score
│                 │
└──────────┬──────┘
           ↓
Temporal analysis
           ↓
A/V synchronization
           ↓
Identity consistency
           ↓
Evidence fusion
           ↓
Evidence stability
           ↓
Continuous risk engine
           ↓
┌──────────┬──────────────┬───────────────┐
│          │              │               │
Alert      Heatmap        Timeline        Evidence graph
│          │              │               │
└──────────┴──────────────┴───────────────┘
                         ↓
                 Forensic report
                         ↓
                  Tamper-evident log
```

---

# 3. REQUIRED TECHNOLOGY STACK

Use the following stack unless there is a technically justified reason to substitute something.

### Frontend

- Next.js
- React
- TypeScript
- Tailwind CSS
- WebRTC
- WebSocket client
- Recharts or equivalent charting library

### Backend

- Python
- FastAPI
- Pydantic
- WebSockets

### ML

- PyTorch
- torchvision
- torchaudio where appropriate
- OpenCV
- NumPy
- SciPy
- librosa if needed

### Database

- PostgreSQL

### Caching / asynchronous work

- Redis

### Media

- FFmpeg
- FFprobe

### Containerization

- Docker
- Docker Compose

### Testing

- Pytest
- Playwright

Do not introduce Kubernetes unless specifically needed.
Do not introduce microservices for every tiny component.
Keep the hackathon architecture understandable.

---

# 4. HARDWARE ASSUMPTION

The primary development machine has an NVIDIA RTX 5050 GPU.

The system must:

1. Detect whether CUDA is available.
2. Detect GPU name.
3. Expose inference device through configuration.
4. Fall back to CPU gracefully.
5. Never crash simply because CUDA is unavailable.
6. Log GPU memory usage where feasible.
7. Allow model device selection using environment variables.

Example:

```env
DEVICE=cuda
```

or:

```env
DEVICE=cpu
```

Add startup diagnostics:

- GPU available
- GPU name
- CUDA version if accessible
- PyTorch version
- model versions

Do not hard-code a particular CUDA version.

Tell the developer to install PyTorch using the current official PyTorch installation instructions appropriate for the machine.

---

# 5. REPOSITORY STRUCTURE

Create this high-level structure and improve it only when necessary:

```text
media-integrity/
│
├── frontend/
├── backend/
├── ml/
│   ├── visual/
│   ├── audio/
│   ├── temporal/
│   ├── avsync/
│   ├── identity/
│   └── fusion/
├── preprocessing/
├── training/
├── models/
├── datasets/
├── forensic/
├── audit/
├── reports/
├── scripts/
├── tests/
├── docs/
├── docker/
├── .env.example
├── docker-compose.yml
├── README.md
└── AGENTS.md
```

Also create:

- `docs/architecture.md`
- `docs/implementation-plan.md`
- `docs/model-registry.md`
- `docs/datasets.md`
- `docs/security.md`
- `docs/privacy.md`
- `docs/licenses.md`
- `docs/performance-report.md`
- `docs/demo-guide.md`
- `docs/limitations.md`

---

# 6. CREATE AGENTS.md

Create `AGENTS.md` in the repository root.

It must contain:

- project purpose
- architecture rules
- coding style
- security rules
- ML model boundaries
- testing requirements
- no-fake-results rule
- licensing rule
- privacy rule
- how frontend/backend/ML layers communicate

Rules:

- The frontend must never import ML code.
- The backend must never contain frontend UI logic.
- ML inference must be exposed through stable interfaces.
- Models may be replaced without modifying API contracts.

---

# 7. BEFORE WRITING IMPLEMENTATION CODE

First inspect the current repository.

If empty, initialize the project.

Then create:

1. architecture diagram
2. implementation plan
3. data contracts
4. API contract
5. database schema
6. ML interface specification
7. risk-state specification
8. testing strategy

Do not start deep implementation until these artifacts exist.

After creating them, execute the plan in phases.

Do not wait for user confirmation between phases unless blocked by credentials, unavailable model weights, or an actual safety/security decision.

---

# 8. IMPORTANT MODEL POLICY

Use established/open implementations as baselines.

Potential model families:

### Face detection

- SCRFD

### Identity embedding

- ArcFace

### Visual manipulation

- EfficientNet-B0 initially
- EfficientNet-B4 later
- optionally a ViT-based detector later

### Audio spoof

- AASIST-L initially
- RawNet2 optionally

### Audio-video synchronization

- SyncNet-style synchronization model

### Temporal

- small GRU or small Transformer initially

### Heatmap

- Grad-CAM or suitable attribution method

### Provenance

- C2PA

Do not assume every repository, checkpoint, or dataset has the same license.

For every external model record:

- repository
- model name
- checkpoint source
- license
- citation
- download instructions
- expected input format
- expected output format
- whether commercial redistribution is allowed

Create `docs/model-registry.md` with:

```text
Model
Purpose
Source
Checkpoint
License
Input
Output
Device
Approximate latency
Status
```

Statuses:

- AVAILABLE
- NOT_DOWNLOADED
- LICENSE_REVIEW_REQUIRED
- CPU_ONLY
- CUDA_READY
- EXPERIMENTAL

If the model cannot legally or technically be used, do not silently substitute fake weights.

Instead:

- implement the adapter
- provide clear setup instructions
- create a deterministic test stub ONLY for unit tests
- mark the stub clearly as NOT FOR REAL INFERENCE

Never fabricate ML output.

---

# 9. DATASET POLICY

Do not automatically download large datasets without checking:

- license
- storage size
- network requirements
- intended usage

Potential research datasets:

- FaceForensics++
- DFDC
- ASVspoof

Use them only when their applicable terms allow the intended usage.

Create `datasets/README.md` documenting:

- dataset
- task
- license
- train split
- validation split
- test split
- identity separation strategy

CRITICAL:

Split by source video / identity rather than random frame.

Never put frames from the same source video into both train and test.

The training pipeline must fail or warn if severe data leakage is detected.

---

# 10. VISUAL PIPELINE

Build:

```text
WebRTC frame
  ↓
Frame sampling
  ↓
Face detector
  ↓
Face alignment
  ↓
Face crop
  ↓
Visual deepfake detector
  ↓
Frame score
```

Use approximately 5 FPS as the initial analysis rate.

Do not force 30 FPS AI inference.

The live pipeline must prioritize fresh data.

If processing falls behind:
- drop stale frames
- do not build an unbounded queue

Create:

`ml/visual/detector.py`

Interface:

```python
class VisualDetector:
    def predict(self, image) -> DetectionResult:
        ...
```

`DetectionResult` must include:

- score
- model_version
- processing_time_ms
- optional bounding_box
- optional landmarks
- status

---

# 11. FACE DETECTION

Use SCRFD or equivalent.

Output:

- bbox
- confidence
- keypoints

Do not run the deepfake classifier on the whole 1080p frame by default.

Use the detected face region.

Support:

- one face
- multiple faces
- no face

If no face exists:

```text
NO_FACE_DETECTED
```

Do not convert that to fake/authentic.

---

# 12. MULTIPLE FACE SUPPORT

For multiple faces:

- face_1
- face_2
- face_3

Track them over time.

Each track gets:

- track_id
- bbox
- identity score if enabled
- visual score
- temporal score

The system must never mix evidence from unrelated faces.

Example:

```text
Track 1 → suspicious
Track 2 → normal
```

The UI must show which track generated the event.

---

# 13. VISUAL MODEL

Initial model:

**EfficientNet-B0**

Then support:

**EfficientNet-B4**

Model adapter:

`ml/visual/efficientnet_detector.py`

Input:
- aligned face crop

Output:
- raw logits
- class score

Never present raw model output directly as calibrated probability.

Store:

`raw_score`

Then calibration converts it to:

`calibrated_score`

Calibration must be implemented separately.

---

# 14. SECOND VISUAL MODEL

Implement an adapter interface for a second detector.

Preferred direction:

- ViT / UIA-ViT or another documented detector supported by the selected benchmark/framework

Do not make the entire system depend on the second model.

If unavailable:
- disable it gracefully

Model disagreement must be recorded.

Example:

```text
visual_model_a = 0.91
visual_model_b = 0.38

model_disagreement = HIGH
```

This becomes a feature for uncertainty.

---

# 15. AUDIO PIPELINE

```text
Remote WebRTC audio
  ↓
AudioWorklet/browser audio capture
  ↓
PCM
  ↓
resampling
  ↓
voice activity detection
  ↓
1-second sliding windows
  ↓
audio spoof model
  ↓
voice anomaly score
```

Initial window:
- approximately 1 second

Initial hop:
- approximately 0.5 second

Make both configurable.

Do not run inference if no speech is detected.

Return:

`NO_SPEECH`

rather than score = 0.

---

# 16. AUDIO MODEL

Initial model:

**AASIST-L** or another verified lightweight anti-spoofing checkpoint.

Interface:

```python
class AudioDetector:
    def predict(
        self,
        audio: np.ndarray,
        sample_rate: int
    ) -> DetectionResult:
        ...
```

Use a second model such as RawNet2 only as an optional independent signal.

Record:

- audio_score
- model_version
- window_start
- window_end
- latency

---

# 17. TEMPORAL ANALYSIS

Do not initially use a very large video transformer.

Take features from successive frames:

```text
e1
e2
e3
...
e16
```

Use:

- small GRU or Transformer

Output:

`temporal_anomaly_score`

Track:

- embedding change
- landmark change
- head motion change
- face bounding-box continuity

The temporal detector must operate on a rolling window.

---

# 18. AUDIO-VIDEO SYNCHRONIZATION

Implement a synchronization module.

Inputs:

- mouth motion sequence
- audio sequence
- timestamps

Output:

`av_sync_score`

Clearly define score semantics in code.

For example:

- high score = good synchronization

Choose ONE convention and use it everywhere.

Do not mix `sync_score` and `inverse_sync_score` without clear naming.

If score semantics need inversion during fusion:

```text
contradiction_score = 1 - sync_score
```

Document this.

---

# 19. IDENTITY CONSISTENCY

Make ArcFace an optional signal.

Flow:

```text
reference identity
  ↓
embedding
  ↓
live face
  ↓
embedding
  ↓
cosine similarity
```

Output:

`identity_similarity`

Do not treat low similarity automatically as deepfake.

Possible causes:

- pose
- occlusion
- lighting
- resolution
- different person
- tracking error

Therefore:

`identity_mismatch` is only evidence.

---

# 20. CROSS-MODAL EVIDENCE ENGINE

This is a critical module.

Create:

`forensic/cross_modal.py`

Input:

- visual evidence
- audio evidence
- temporal evidence
- A/V synchronization evidence
- identity evidence

It must detect contradictions such as:

- visual suspicious + audio normal
- visual normal + audio suspicious
- strong voice anomaly + poor lip/audio synchronization
- identity mismatch + face manipulation evidence
- suspicious events occurring in the same time interval

Output:

`CrossModalEvent`

Fields:

- event_id
- start_time
- end_time
- signals
- severity
- agreement
- explanation

Example:

```json
{
  "event": "cross_modal_contradiction",
  "start_time": 17.4,
  "end_time": 19.8,
  "signals": [
    "visual_anomaly",
    "voice_anomaly",
    "low_av_sync"
  ],
  "severity": "high"
}
```

---

# 21. EVIDENCE FUSION

Create:

`ml/fusion/fusion_engine.py`

Inputs:

- visual_score
- audio_score
- temporal_score
- av_sync_score
- identity_similarity
- model_disagreement
- provenance features

Start with a transparent weighted model or logistic regression.

Do not immediately claim probabilistic meaning.

Output:

`raw_risk_score`

Then pass through calibration.

Final:

`calibrated_risk_score`

And classification:

- LIKELY_AUTHENTIC
- INCONCLUSIVE
- LIKELY_MANIPULATED

Thresholds must be configurable.

Keep thresholds in configuration, not buried inside code.

---

# 22. RISK STATE MACHINE

Implement:

- NORMAL
- WATCH
- ELEVATED
- HIGH

Flow:

```text
NORMAL
  ↓ persistent anomaly
WATCH
  ↓ stronger/persistent evidence
ELEVATED
  ↓ multimodal agreement
HIGH
```

Also implement recovery:

```text
HIGH
  ↓ evidence disappears
ELEVATED
  ↓
WATCH
  ↓
NORMAL
```

Do not trigger HIGH from one frame.

Use temporal persistence.

Example configurable settings:

- `MIN_SUSPICIOUS_WINDOWS`
- `MIN_MULTIMODAL_AGREEMENT`
- `HIGH_RISK_DURATION`
- `RECOVERY_DURATION`

---

# 23. CONTINUOUS TRUST TIMELINE

Store risk over time:

- timestamp
- risk score
- risk state

Example:

```text
00:00 → 0.12
00:05 → 0.14
00:10 → 0.18
00:15 → 0.42
00:17 → 0.72
00:18 → 0.84
00:19 → 0.87
```

Expose this through an API.

Frontend displays a live graph.

---

# 24. EVIDENCE STABILITY ENGINE

This is one of the major differentiating components.

When a suspicious event reaches ELEVATED/HIGH:

1. Take a representative media segment.
2. Generate controlled transformations:
   - original
   - resize
   - JPEG compression
   - mild noise
   - mild blur
   - crop
3. Re-run the detector.
4. Compare results.
5. Calculate `stability_score`.

Example:

```text
Original 0.90
JPEG     0.88
Resize   0.86
Noise    0.84
Crop     0.87
```

→ HIGH STABILITY

If results vary substantially:

→ LOW STABILITY

Then update interpretation:

- HIGH risk + HIGH stability → stronger evidence
- HIGH risk + LOW stability → INCONCLUSIVE / reduced confidence

Do not let the stability engine secretly modify raw model outputs.

Store both:
- raw result
- stability-adjusted interpretation

---

# 25. MEDIA DNA

Create:

`forensic/media_dna.py`

Generate:

- cryptographic hash
- perceptual image/frame fingerprint
- audio fingerprint
- temporal fingerprint
- codec metadata
- duration
- resolution
- frame rate

For live media, create segment fingerprints.

The goal is to enable future similarity clustering.

Do not implement a giant distributed similarity database yet.

Start with:
- exact match
- perceptual similarity
- local PostgreSQL storage

---

# 26. C2PA / PROVENANCE

Create:

`forensic/provenance.py`

When media has C2PA metadata:
- read and validate it

Report:

- C2PA_PRESENT
- C2PA_VALID
- C2PA_INVALID
- C2PA_UNAVAILABLE

Never interpret `C2PA missing` as fake.

Provenance evidence and AI forensic evidence must remain separate.

---

# 27. FORENSIC EVIDENCE GRAPH

Represent relationships:

```text
CALL
 ↓
PARTICIPANT
 ↓
TIME SEGMENT
 ↓
VISUAL EVENT
 ↓
AUDIO EVENT
 ↓
A/V EVENT
 ↓
FUSION EVENT
 ↓
RISK ESCALATION
```

Example:

```text
CALL-001
 └── participant-2
      └── 17.4–19.8s
           ├── visual anomaly
           ├── voice anomaly
           ├── temporal anomaly
           ├── low A/V sync
           └── high-risk event
```

Provide a JSON API for the graph.

Frontend can initially visualize it as a structured evidence panel instead of requiring a complicated graph library.

---

# 28. HEATMAP

Implement Grad-CAM or another valid model-attribution method.

Pipeline:

```text
frame
 ↓
model
 ↓
attribution
 ↓
heatmap
 ↓
overlay
```

Store:

- frame_timestamp
- model_version
- heatmap_path
- original_frame_path

UI:

- Original
- Heatmap
- Overlay

Add disclaimer:

> Attribution visualization shows regions that contributed to the model prediction; it is not independent proof of manipulation.

---

# 29. LIVE WEBRTC APPLICATION

Build a simple two-party WebRTC call.

Requirements:

- user names
- room ID
- local preview
- remote video
- mute
- camera on/off
- leave call
- connection state
- analysis status

Use FastAPI WebSocket signaling initially.

Implement:
- offer
- answer
- ICE candidate exchange

Use STUN configuration.

For local development, allow LAN operation.

Do not depend on Zoom/Teams for the core demo.

---

# 30. REMOTE VIDEO ANALYSIS

In browser:

```text
remote video
  ↓
canvas sampling
  ↓
~5 FPS
  ↓
JPEG compression
  ↓
WebSocket
  ↓
FastAPI
```

Do not stream raw 1080p frames continuously.

The browser should:
- drop frames if backend is busy
- keep the latest frame
- prevent unbounded queues

---

# 31. REMOTE AUDIO ANALYSIS

Use Web Audio API / AudioWorklet for the analysis branch.

Do not create a second audible playback path accidentally.

Flow:

```text
remote WebRTC track
  ↓
analysis branch
  ↓
AudioWorklet
  ↓
PCM chunks
  ↓
WebSocket
```

Make sure:
- no echo
- no duplicated audio
- no feedback loop

---

# 32. LIVE ANALYSIS WEBSOCKET PROTOCOL

Implement:

```text
/ws/analyze/video/{call_id}
/ws/analyze/audio/{call_id}
/ws/results/{call_id}
```

Video input message:

- JPEG frame
- timestamp
- participant_id

Audio input:

- PCM chunk
- sample rate
- timestamp
- participant_id

Result format:

```json
{
  "type": "risk_update",
  "call_id": "CALL-001",
  "participant_id": "P2",
  "timestamp": 17.8,
  "visual": 0.89,
  "audio": 0.91,
  "temporal": 0.77,
  "av_sync": 0.24,
  "identity_similarity": 0.42,
  "risk_score": 0.86,
  "risk_state": "HIGH"
}
```

All numeric fields must explicitly document their direction and meaning.

---

# 33. BACKPRESSURE

This is mandatory.

Implement bounded queues.

For live video:

`MAX_VIDEO_QUEUE_SIZE`

For audio:

`MAX_AUDIO_QUEUE_SIZE`

If video queue is full:
- drop oldest unprocessed frame

If audio queue is full:
- prefer dropping stale windows rather than crashing

Record:

- dropped_frame_count
- dropped_audio_window_count

Show processing health.

---

# 34. GPU WORKER

Separate transport from inference.

Flow:

```text
WebSocket
 ↓
bounded queue
 ↓
GPU worker
 ↓
model
 ↓
result queue
 ↓
WebSocket output
```

Do not run expensive inference directly in a blocking WebSocket loop.

---

# 35. INITIAL PERFORMANCE STRATEGY

Continuous:

- SCRFD
- EfficientNet-B0
- AASIST-L
- small temporal analysis

Triggered:

- EfficientNet-B4
- second visual detector
- second audio detector
- Grad-CAM
- evidence stability

This must be configuration-driven.

Example:

```env
ENABLE_HEAVY_MODELS=true
HEAVY_MODEL_TRIGGER=0.65
```

Do not claim actual latency until measured.

---

# 36. LATENCY METRICS

Measure:

- capture latency
- preprocessing latency
- face detection latency
- visual inference latency
- audio inference latency
- fusion latency
- WebSocket latency
- end-to-end alert latency

Store moving averages.

Dashboard:

```text
Video inference: xx ms
Audio inference: xx ms
End-to-end:      xx ms
Dropped frames:  xx
```

Do not invent benchmark numbers.

Create:

`docs/performance-report.md`

with measured:

- FPS
- latency
- GPU utilization
- VRAM
- CPU
- RAM
- dropped frames
- alert latency

---

# 37. FRONTEND DASHBOARD

Create a professional security/forensics dashboard.

Layout:

```text
┌──────────────────────────────────────────────────────────┐
│ SECURECALL                                               │
│ Live Media Integrity                                     │
├──────────────────────────────┬───────────────────────────┤
│                              │                           │
│        REMOTE VIDEO          │     MEDIA INTEGRITY       │
│                              │                           │
│                              │ Video             0.89    │
│                              │ Audio             0.91    │
│                              │ Temporal          0.77    │
│                              │ A/V               0.24    │
│                              │ Identity          0.42    │
│                              │                           │
│                              │ ⚠ HIGH RISK              │
├──────────────────────────────┴───────────────────────────┤
│ Risk Timeline                                            │
│                                                          │
│ 00:00──────10──────20──────30──────40──────60            │
│                         ███████                           │
├──────────────────────────────────────────────────────────┤
│ Evidence                                                 │
│                                                          │
│ [Heatmap] [Audio] [A/V Sync] [Provenance] [Stability]  │
└──────────────────────────────────────────────────────────┘
```

Do not overload the screen with raw model jargon.

Use tooltips/explanations.

---

# 38. ALERT DESIGN

Possible statuses:

GREEN:
`LOW RISK`

YELLOW:
`WATCH`

ORANGE:
`ELEVATED MANIPULATION EVIDENCE`

RED:
`HIGH MANIPULATION EVIDENCE`

Wording must be evidence-based.

Avoid:

`PERSON IS FAKE`

Use:

`High manipulation evidence detected`

or:

`Possible synthetic media detected`

---

# 39. EVIDENCE PANEL

When clicking a suspicious event, show:

```text
Event:
Cross-modal contradiction

Time:
17.4–19.8 sec

Visual:
0.89

Audio:
0.91

A/V:
0.24

Temporal:
0.77

Identity:
0.42

Evidence stability:
HIGH
```

Then show:

- heatmap
- representative frame
- audio evidence
- timeline
- model versions

---

# 40. BULK MEDIA VERIFICATION

Implement:

`POST /api/v1/bulk`

Accept:
- ZIP / multiple files

Pipeline:

```text
upload
 ↓
validation
 ↓
hash
 ↓
job creation
 ↓
parallel processing
 ↓
fusion
 ↓
CSV/JSON summary
```

Dashboard:

- Files
- Processed
- Errors
- Likely Authentic
- Inconclusive
- Likely Manipulated

---

# 41. FORENSIC REPORT

Generate both:

- JSON
- PDF/HTML

Report fields:

- Analysis ID
- Timestamp
- Media SHA-256
- Media type
- Duration
- Model versions
- Raw detector results
- Calibrated scores
- Suspicious intervals
- Heatmaps
- A/V results
- Identity results
- Provenance
- Stability results
- Final assessment
- Limitations
- Audit information

Include this warning:

> This report is an automated forensic assessment based on the analyzed media and configured models. It should be treated as decision support and may contain false positives or false negatives.

---

# 42. AUDIT LOG

Create a tamper-evident hash chain.

Events:

- CALL_CREATED
- MEDIA_RECEIVED
- ANALYSIS_STARTED
- FRAME_ANALYZED
- AUDIO_WINDOW_ANALYZED
- ANOMALY_DETECTED
- RISK_ESCALATED
- REPORT_CREATED

Each event contains:

- event_id
- timestamp
- event_type
- call_id
- payload_hash
- previous_hash
- current_hash

Hash:

```text
SHA-256(canonical_event_json + previous_hash)
```

Implement:

`GET /api/v1/calls/{call_id}/audit/verify`

Response:

- valid
- broken_at_event
- expected_hash
- actual_hash

---

# 43. MEDIA HASH

When media enters the system:

calculate SHA-256.

Store:

`media_sha256`

This hash must appear in:

- database
- report
- audit chain

Do not hash only the filename.

Hash the actual bytes.

---

# 44. SECURITY

Implement:

- MIME/type validation
- maximum upload size
- maximum video duration
- maximum ZIP extraction size
- path traversal protection
- randomized storage names
- rate limiting
- WebSocket authentication/session validation
- input validation
- safe filename handling
- temporary-file cleanup
- configurable retention
- CORS restrictions
- no arbitrary command execution from user input

Use FFmpeg safely.

Never interpolate arbitrary user input directly into shell commands.

Use subprocess argument arrays.

---

# 45. PRIVACY

The system must clearly distinguish:

`LIVE ANALYSIS`

and

`STORED EVIDENCE`

Default to minimizing storage.

For live calls:
- keep a short rolling buffer

When a suspicious event crosses a configured threshold:
- capture only the relevant evidence segment if configured

Make retention configurable:

```env
RETENTION_MODE=ephemeral
```

or:

```env
RETENTION_MODE=24h
```

The UI must state that live-call media may be processed.

---

# 46. CONSENTED DEMO MODE

Create a development flag:

```env
DEMO_MODE=true
```

In demo mode show:

`CONTROLLED SYNTHETIC MEDIA TEST`

The synthetic-media test uses:

- consenting teammates
- controlled face-swap input
- controlled synthetic audio
- optionally lip-sync manipulation

Do not integrate with or bypass third-party biometric security systems.

The face-swap generator is only an attack fixture for testing the defensive detector.

---

# 47. DEMO ATTACK SCENARIOS

Create documented test fixtures.

### Scenario A
REAL VIDEO + REAL AUDIO

Expected:
- low risk

### Scenario B
CONTROLLED FACE-SWAP VIDEO + REAL AUDIO

Expected:
- visual anomaly

### Scenario C
REAL VIDEO + CONTROLLED SYNTHETIC VOICE

Expected:
- audio anomaly

### Scenario D
CONTROLLED FACE-SWAP VIDEO + SYNTHETIC VOICE

Expected:
- multimodal high-risk evidence

### Scenario E
REAL VIDEO + AUDIO/VIDEO TIMING DISTURBANCE

Expected:
- A/V inconsistency

### Scenario F
REPLAYED VIDEO

Expected:
- possible replay/injection indicators, if implemented

Do not hard-code expected results into the detector.

These expectations belong in tests and evaluation reports.

---

# 48. FACE-SWAP TEST SOURCE

The project may use a consent-based open-source face-swap application or controlled offline test footage.

Do not build face swapping as part of the production system.

Document:

- source
- license
- test configuration
- consent
- output labeling

The detector must not depend on knowing which face-swapping program generated the test sample.

---

# 49. TESTING STRATEGY

Create three testing levels.

## LEVEL 1 — Unit tests

Test:
- hash chain
- fusion
- state machine
- calibration
- input validation
- Media DNA
- score serialization
- WebSocket schema
- stability calculation

## LEVEL 2 — Integration tests

Test:
- frontend
- WebRTC signaling
- video WebSocket
- audio WebSocket
- GPU worker
- database
- report generation

## LEVEL 3 — End-to-end

Test:

1. browser A joins call
2. browser B joins call
3. remote video appears
4. remote audio appears
5. analysis starts
6. risk updates arrive
7. event generated
8. timeline updated
9. evidence report generated
10. audit verifies

---

# 50. MODEL TESTING

For each detector report:

- accuracy
- precision
- recall
- F1
- ROC-AUC
- PR-AUC where appropriate
- false-positive rate
- false-negative rate

Audio anti-spoofing:
include task-appropriate metrics such as EER where benchmark methodology supports it.

Also test:

- compression
- resize
- noise
- blur
- low-resolution
- different lighting
- different identities
- unseen source videos

---

# 51. DATA LEAKAGE TEST

Create a test that checks:

same source video must not appear in train and test.

If metadata allows, track:

- source_video_id
- identity_id

Fail validation on severe overlap.

---

# 52. NO-FACE / NO-SPEECH HANDLING

Video with no detectable face:

`status = NOT_APPLICABLE`

Audio with no speech:

`status = NO_SPEECH`

Multiple faces:

analyze each track independently.

Blurred face:

`status = LOW_QUALITY`

Do not infer fake from missing evidence.

---

# 53. MODEL FAILURE HANDLING

If a model fails:

Do not crash the whole call.

Return:

`model_status = ERROR`

and continue with remaining modalities.

Example:

```text
visual = available
audio = available
temporal = unavailable
A/V = available
```

Fusion must account for missing modalities.

Never treat missing modality as zero.

---

# 54. UNCERTAINTY

Implement uncertainty factors:

- model disagreement
- missing modality
- low-quality input
- low stability
- insufficient duration
- insufficient face visibility

These should all increase uncertainty.

The final system must be capable of returning:

`INCONCLUSIVE`

---

# 55. DATABASE

Use PostgreSQL.

Tables:

- users
- calls
- participants
- media
- analysis_jobs
- frame_results
- audio_results
- temporal_results
- av_sync_results
- fusion_results
- risk_events
- evidence_artifacts
- media_dna
- provenance
- reports
- audit_logs
- model_versions

Create proper indexes.

Important indexes:

- calls.id
- analysis_jobs.call_id
- frame_results.job_id
- risk_events.call_id
- audit_logs.call_id
- media.sha256

---

# 56. REST API

Implement:

```text
POST /api/v1/calls
GET /api/v1/calls/{call_id}
POST /api/v1/media/upload
POST /api/v1/verify
GET /api/v1/verify/{job_id}
GET /api/v1/calls/{call_id}/events
GET /api/v1/calls/{call_id}/timeline
GET /api/v1/calls/{call_id}/evidence
GET /api/v1/calls/{call_id}/report
GET /api/v1/calls/{call_id}/audit
GET /api/v1/calls/{call_id}/audit/verify
POST /api/v1/bulk
GET /api/v1/models
GET /api/v1/health
GET /api/v1/metrics
```

Generate OpenAPI documentation automatically.

---

# 57. ERROR CONTRACT

All API errors must have:

- code
- message
- details
- request_id

Example:

```json
{
  "code": "NO_FACE_DETECTED",
  "message": "No suitable face was detected for visual analysis.",
  "request_id": "..."
}
```

---

# 58. OBSERVABILITY

Implement structured logging.

Each log must include:

- timestamp
- request_id
- call_id if present
- participant_id if present
- component
- event
- latency
- status

Avoid logging:
- raw audio
- raw video
- secrets
- API keys

unless explicitly in secure development mode.

---

# 59. CONFIGURATION

Create `.env.example`:

```env
APP_ENV=development
DEBUG=true

DEVICE=cuda

DATABASE_URL=...
REDIS_URL=...

VIDEO_SAMPLE_FPS=5
AUDIO_WINDOW_SECONDS=1.0
AUDIO_HOP_SECONDS=0.5

ENABLE_ARCFACE=true
ENABLE_SECOND_VISUAL_MODEL=false
ENABLE_SECOND_AUDIO_MODEL=false
ENABLE_C2PA=true
ENABLE_STABILITY_TEST=true

HIGH_RISK_THRESHOLD=...
ELEVATED_THRESHOLD=...

MAX_UPLOAD_MB=...
MAX_VIDEO_SECONDS=...

RETENTION_MODE=ephemeral
```

Never hard-code secrets.

---

# 60. FRONTEND ROUTES

Create:

```text
/
/call/{roomId}
/dashboard
/cases/{caseId}
/bulk
/reports/{reportId}
/settings
```

### Landing page
Simple product explanation + enter call.

### Call page
Live call + integrity dashboard.

### Dashboard
Past analyses.

### Case page
Full forensic evidence.

### Bulk
File processing dashboard.

### Report page
Forensic report.

---

# 61. DESIGN REQUIREMENTS

Professional cybersecurity/forensics aesthetic.

Prioritize:

- clarity
- readability
- evidence hierarchy
- low visual clutter

Use:

- dark/light theme
- clear status indicators
- timeline
- cards
- expandable evidence
- badges for model states
- latency indicators

Do not make it look like a generic AI chatbot.

It should look like a:

**security operations / forensic analysis product**

---

# 62. LIVE CALL UX

Top:
- participant status

Center:
- remote video

Side:
- risk panel

Bottom:
- timeline

When risk becomes ELEVATED or HIGH:
show non-blocking warning banner.

Do not automatically terminate the call.

For high-risk events provide:

- Review Evidence
- Verify Through Trusted Channel

rather than automatic punitive action.

---

# 63. PERFORMANCE REQUIREMENTS

The prototype must attempt to achieve:

- responsive call playback
- bounded queues
- asynchronous inference
- GPU batching where practical
- stale-frame dropping
- no blocking UI
- no unbounded memory growth

Measure actual results.

Do not invent performance figures.

---

# 64. CPU FALLBACK

The entire application must run without GPU for:

- API
- frontend
- call setup
- tests
- database

Model inference can be slower.

Show:

`GPU unavailable — CPU inference mode`

Do not silently fail.

---

# 65. MODEL WARMUP

At application startup:

- load required models once

Do not reload the model for every frame.

Use a singleton/model manager or controlled dependency lifecycle.

Log:

- model loaded
- model version
- device
- load time

---

# 66. BATCH INFERENCE

When possible:

```text
frame 1 face
frame 2 face
frame 3 face
...
batch → GPU
```

Do not sacrifice live freshness for enormous batch sizes.

Make batch size configurable.

---

# 67. ADAPTIVE ANALYSIS

Implement a two-stage strategy.

### Stage 1
Lightweight continuous screening.

### Stage 2
Heavy models when suspicion passes threshold.

Example:

LOW:
- SCRFD
- EfficientNet-B0
- AASIST-L

SUSPICIOUS:
- EfficientNet-B4
- second visual detector
- second audio detector
- Grad-CAM
- stability analysis

This should reduce GPU use.

---

# 68. FUSION MISSING-MODALITY LOGIC

### VIDEO ONLY

Use:
- visual
- temporal
- identity

### AUDIO ONLY

Use:
- audio

### VIDEO + AUDIO

Use:
- visual
- audio
- temporal
- A/V
- identity if enabled

Never penalize a file just because it lacks a modality.

---

# 69. REPORT EXPLANATION ENGINE

Generate a human-readable explanation from structured evidence.

Do **not** use an LLM to fabricate forensic conclusions.

Use deterministic templates.

Example:

> Visual analysis detected elevated anomaly evidence across 23 sampled frames.

> Audio analysis detected elevated synthetic-speech evidence in the 17.0–19.0 second interval.

> Audio-video synchronization was poor during the same interval.

> Evidence stability remained high across tested transformations.

This explanation must be generated from actual structured fields.

---

# 70. NO HALLUCINATED EVIDENCE

This rule is mandatory.

Never write:

`Face boundary anomaly detected`

unless the visual analysis actually generated that evidence.

Never write:

`Voice clone detected`

unless the audio model actually returned evidence.

Never generate fake confidence.

Never fake a heatmap.

If something is unavailable:

say it is unavailable.

---

# 71. MODEL VERSIONING

Every inference must store:

- model_name
- model_version
- checkpoint_hash
- preprocessing_version

For example:

- visual_detector v1.0.0
- audio_detector v1.0.0
- fusion v1.0.0

Old reports must preserve original model versions.

---

# 72. REPRODUCIBILITY

For every case, store enough information to reproduce the analysis where possible.

Include:

- media hash
- model versions
- configuration version
- sampling rate
- analysis settings
- timestamp

Do not rely on "whatever model is currently installed."

---

# 73. LEGAL / LICENSING DOCUMENTATION

Create:

`docs/licenses.md`

For every dependency:

- package
- version
- license
- purpose

For every model:

- code license
- weight license
- dataset license

If unsure:

mark:

`LICENSE_REVIEW_REQUIRED`

Do not falsely claim open-source/commercial rights.

---

# 74. DEMO SETUP

Create a one-command demo setup:

```bash
./scripts/start_demo.sh
```

Then:

1. start PostgreSQL
2. start Redis
3. start backend
4. start frontend
5. verify health
6. display URLs

Do not automatically launch face-swapping software.

The synthetic-media source is controlled separately by the team.

---

# 75. E2E DEMO TEST

Create automated test:

1. open browser A
2. open browser B
3. join same room
4. verify remote stream
5. send analysis frames
6. receive risk events
7. simulate suspicious detector output using deterministic test fixture
8. verify UI changes to ELEVATED
9. verify evidence event
10. verify timeline
11. verify audit chain
12. verify report

This test must prove the complete software pipeline.

The test fixture may use deterministic synthetic detector responses.

Do **not** use fake results in the actual production inference path.

---

# 76. REAL MODEL INTEGRATION TEST

When checkpoints are available:

- run one real image through visual model
- run one real audio sample through audio model
- run one real synchronized sample through A/V module

Print:

- input shape
- output shape
- latency
- device
- score

Fail if model returns invalid numerical values.

---

# 77. HEALTH ENDPOINT

`GET /api/v1/health`

Return:

```json
{
  "backend": "ok",
  "database": "ok",
  "redis": "ok",
  "gpu": {
    "available": true,
    "name": "...",
    "memory": "..."
  },
  "models": {
    "visual": "ready",
    "audio": "ready",
    "sync": "ready"
  }
}
```

---

# 78. BROWSER VERIFICATION

After the application is running, use browser automation to verify:

- landing page loads
- call page loads
- camera/microphone permissions are handled
- room connection works
- remote video renders
- integrity panel renders
- risk timeline renders
- evidence panel opens
- report page works
- audit verification works

Fix frontend/runtime issues rather than merely reporting them.

---

# 79. FAILURE SCENARIOS TO TEST

Test all of these:

- invalid image
- corrupt video
- missing audio
- no speech
- no face
- multiple faces
- blurred face
- camera disabled
- microphone disabled
- WebRTC disconnect
- WebSocket disconnect
- GPU unavailable
- model unavailable
- database unavailable
- Redis unavailable
- large upload
- malformed ZIP
- duplicate media
- long video
- high FPS
- low FPS

The UI must fail gracefully.

---

# 80. DOCUMENTATION TO GENERATE

Create:

`README.md`

and:

```text
docs/
  architecture.md
  implementation-plan.md
  API.md
  model-registry.md
  datasets.md
  security.md
  privacy.md
  licenses.md
  performance-report.md
  demo-guide.md
  limitations.md
```

Also create:

`docs/demo-script.md`

explaining the exact 5-minute hackathon demonstration.

---

# 81. DEMO SCRIPT

The final demo should be:

### STEP 1
Start normal call.

UI:
`LOW RISK`

### STEP 2
Introduce controlled face-swap stream.

UI:
visual anomaly increases.

### STEP 3
Continue call.

Temporal score increases.

### STEP 4
Introduce controlled synthetic voice.

Audio score increases.

### STEP 5
A/V sync becomes inconsistent.

### STEP 6
Fusion changes to ELEVATED/HIGH.

### STEP 7
Click:

`VIEW EVIDENCE`

Show:

- suspicious timestamp
- representative frame
- heatmap
- audio evidence
- A/V evidence
- identity evidence if enabled
- stability result
- model agreement

### STEP 8
Open forensic report.

### STEP 9
Verify audit chain.

The entire demonstration must use consenting teammates and clearly labeled controlled synthetic media.

---

# 82. WHAT COUNTS AS SUCCESS

The project is complete only when all of the following are true:

A. Two browsers can establish a WebRTC call.

B. Remote video appears.

C. Remote audio works.

D. Remote video reaches the analysis pipeline.

E. Remote audio reaches the analysis pipeline.

F. Real model inference works when checkpoints are installed.

G. Results reach the frontend in real time.

H. Timeline updates.

I. Risk state changes based on persistent evidence.

J. Suspicious events are stored.

K. Heatmap generation works for supported visual models.

L. Evidence stability works.

M. Media SHA-256 is generated.

N. Audit hash chain verifies.

O. Report generation works.

P. Bulk verification works.

Q. Browser E2E tests pass.

R. CPU fallback works.

S. Failure cases are handled.

T. Documentation is complete.

---

# 83. IMPLEMENTATION ORDER

Execute in this exact order:

## Phase 1
Repository + documentation + configuration

## Phase 2
Backend skeleton + database + health endpoints

## Phase 3
Frontend skeleton + dashboard

## Phase 4
WebRTC two-party call

## Phase 5
Video capture and WebSocket transport

## Phase 6
Face detection

## Phase 7
Visual model

## Phase 8
Audio capture and WebSocket transport

## Phase 9
Audio model

## Phase 10
Temporal analysis

## Phase 11
A/V synchronization

## Phase 12
Identity consistency

## Phase 13
Fusion engine

## Phase 14
Continuous risk state machine

## Phase 15
Timeline + evidence events

## Phase 16
Heatmaps

## Phase 17
Stability engine

## Phase 18
Media DNA

## Phase 19
C2PA/provenance

## Phase 20
Audit chain

## Phase 21
Reports

## Phase 22
Bulk verification

## Phase 23
Security hardening

## Phase 24
Performance testing

## Phase 25
Browser E2E testing

## Phase 26
Controlled live demo

## Phase 27
Final documentation

Do not skip ahead unnecessarily.

At the end of each phase:

- run tests
- run lint/type checks
- verify actual output
- update `implementation-plan.md`
- record blockers

---

# 84. ANTIGRAVITY AGENT EXECUTION RULES

You are allowed to:

- inspect files
- create files
- modify files
- run terminal commands
- install packages
- launch dev servers
- run tests
- use browser automation
- inspect logs
- fix discovered problems

Before major architecture changes:
update `docs/architecture.md`.

After implementation:
produce:

`docs/final-system-report.md`

Include:

- what works
- what does not
- models installed
- models not installed
- tests passed
- tests failed
- measured latency
- measured resource usage
- known limitations

Do not claim success when a component is only stubbed.

---

# 85. STUB POLICY

A stub is allowed ONLY when:

- a model checkpoint cannot be downloaded automatically
- a license needs review
- hardware does not support a component
- a third-party service credential is unavailable

Every stub must:

- have a clear class/interface
- return status = NOT_AVAILABLE
- never pretend to be genuine inference
- be covered by unit tests
- have replacement instructions

Example:

`NOT_AVAILABLE`

not:

`score = 0.5`

---

# 86. DO NOT OVERENGINEER

Do not:

- build Kubernetes
- introduce Kafka
- introduce blockchain
- train giant foundation models from scratch
- implement 10 visual models initially
- implement every possible video platform
- create unnecessary microservices

Prioritize:

- working
- measurable
- modular
- testable
- explainable

---

# 87. INNOVATION LAYER

The following are the project's differentiating components:

1. Continuous trust trajectory
2. Cross-modal contradiction detection
3. Evidence stability testing
4. Media DNA
5. Evidence graph
6. Tamper-evident forensic history
7. Human-readable forensic explanations

Do not market:

`we use EfficientNet`

as the innovation.

The innovation is:

> **we correlate and stress-test multimodal forensic evidence during a live communication.**

---

# 88. IMPORTANT PRODUCT LIMITATION

The application must clearly state:

The system provides automated forensic evidence and decision support.

It does not guarantee authenticity.

It may fail on:

- unseen generators
- heavy compression
- low-quality media
- novel attacks
- unusual lighting
- severe occlusion
- adversarial manipulation

This limitation must appear in the report.

---

# 89. FINAL ARCHITECTURE TO IMPLEMENT

```text
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
             Temporal model
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

---

# 90. FINAL INSTRUCTION

Start now.

First:

1. inspect repository
2. create `AGENTS.md`
3. create `docs/architecture.md`
4. create `docs/implementation-plan.md`
5. create model registry
6. scaffold frontend/backend/ML modules
7. create Docker Compose
8. create health checks
9. create tests
10. then implement Phase 1 and continue sequentially

Do not stop at scaffolding.

Keep implementing, testing and repairing until the complete MVP pipeline is working.

When a model/checkpoint cannot be legally or technically installed, clearly mark it unavailable and continue implementing the rest of the pipeline.

At the end, provide:

- final architecture
- exact commands to run
- environment variables
- installed models
- missing models
- tests executed
- measured performance
- known limitations
- exact live-demo procedure

Do not fabricate any result, metric, model output, benchmark, or successful integration.

The final objective is a real, locally runnable, end-to-end hackathon prototype—not a conceptual mockup.
