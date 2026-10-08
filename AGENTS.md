# AGENTS.md — Media Integrity / SecureCall

## Project Purpose

**Media Integrity / SecureCall** is a defensive media-integrity and security application that continuously assesses whether media presented during a live communication contains evidence of synthetic generation, manipulation, replay, identity inconsistency, or audio-video inconsistency.

The system provides **decision support**, not absolute truth. It uses evidence-based language:
- `LIKELY AUTHENTIC`
- `INCONCLUSIVE`
- `LIKELY MANIPULATED`

Every model output is treated as **evidence, not truth**.

---

## Architecture Rules

1. **Layer separation is strict:**
   - The **frontend** must NEVER import ML code.
   - The **backend** must NEVER contain frontend UI logic.
   - **ML inference** must be exposed through stable interfaces (Python ABCs / Protocols).
   - Models may be replaced without modifying API contracts.

2. **Communication paths:**
   - Frontend ↔ Backend: REST API + WebSocket
   - Backend → ML: Python function calls through adapter interfaces
   - ML models are loaded once at startup (singleton / model manager)
   - Results flow: ML → Backend → WebSocket → Frontend

3. **No microservices** — monolithic backend with clear module boundaries.
4. **No Kubernetes** — Docker Compose for local development.

---

## Coding Style

### Python (Backend + ML)
- Python 3.11+
- Type hints on all function signatures
- Pydantic models for all data contracts
- `snake_case` for functions and variables
- `PascalCase` for classes
- Docstrings on all public classes/methods
- Structured logging (JSON)
- `black` for formatting, `ruff` for linting

### TypeScript (Frontend)
- TypeScript strict mode
- React functional components with hooks
- `camelCase` for functions/variables, `PascalCase` for components
- Props interfaces for all components
- ESLint + Prettier

---

## Security Rules

- **No arbitrary command execution** from user input
- FFmpeg called via `subprocess` with argument arrays (never string interpolation)
- MIME/type validation on all uploads
- Path traversal protection with randomized storage names
- Rate limiting on all endpoints
- WebSocket authentication/session validation
- CORS restrictions
- Maximum upload sizes enforced
- Never log raw audio, video, secrets, or API keys

---

## ML Model Boundaries

- Every model must have a registered adapter implementing a standard interface
- Every inference must record: `model_name`, `model_version`, `processing_time_ms`, `device`
- Raw scores and calibrated scores are stored separately
- If a model is unavailable, return `status = NOT_AVAILABLE` — never fake inference
- Stubs are allowed ONLY for unit tests and must be clearly marked `NOT FOR REAL INFERENCE`
- No hallucinated evidence — never claim a detection unless the model actually produced it

---

## Testing Requirements

- **Level 1 (Unit):** hash chain, fusion, state machine, calibration, validation, Media DNA
- **Level 2 (Integration):** WebRTC signaling, WebSocket transport, GPU worker, database, reports
- **Level 3 (E2E):** Full browser-based call with analysis pipeline verification
- All tests runnable via `pytest` (backend) and Playwright (E2E)
- Test fixtures may use deterministic synthetic detector responses
- Production inference path must NEVER use fake results

---

## No-Fake-Results Rule

This is mandatory and non-negotiable:
- Never fabricate ML output
- Never generate fake confidence scores
- Never fake a heatmap
- Never write detection claims unless the model actually produced evidence
- If something is unavailable, say it is unavailable

---

## Licensing Rule

- Every external model must have documented: repository, license, checkpoint source, citation
- Every dependency must have documented: package, version, license, purpose
- If license status is uncertain, mark as `LICENSE_REVIEW_REQUIRED`
- Never falsely claim open-source/commercial rights

---

## Privacy Rule

- Distinguish between `LIVE ANALYSIS` (ephemeral) and `STORED EVIDENCE`
- Default to minimizing storage
- Retention mode is configurable (`ephemeral`, `24h`, etc.)
- UI must state that live-call media may be processed
- Face/audio data handled with appropriate consent

---

## Communication Protocol

### Frontend → Backend
- REST API for CRUD operations
- WebSocket for real-time analysis frames and results

### WebSocket Endpoints
- `/ws/analyze/video/{call_id}` — receive video frames
- `/ws/analyze/audio/{call_id}` — receive audio chunks
- `/ws/results/{call_id}` — push analysis results

### Result Format
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
