# Demo Guide — Media Integrity / SecureCall

## Prerequisites

1. Docker and Docker Compose installed
2. NVIDIA GPU with CUDA support (optional — CPU fallback available)
3. PyTorch installed matching your CUDA version
4. Node.js 18+ installed
5. Python 3.11+ installed

## Quick Start

```bash
# Clone and enter the project
cd media-integrity

# Copy environment file
cp .env.example .env

# Start infrastructure (PostgreSQL + Redis)
docker-compose up -d postgres redis

# Start backend
cd backend
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Start frontend (new terminal)
cd frontend
npm install
npm run dev
```

## Demo Script (5-Minute Hackathon Demo)

### Step 1: Normal Call (0:00–1:00)
- Open Browser A at `http://localhost:3000`
- Enter username and room ID
- Open Browser B at `http://localhost:3000`
- Join the same room
- **UI shows:** LOW RISK (green)

### Step 2: Introduce Face-Swap (1:00–2:00)
- Feed controlled face-swap video to Browser B's camera
- **UI shows:** Visual anomaly score increases
- Risk state transitions: NORMAL → WATCH

### Step 3: Temporal Evidence (2:00–2:30)
- Continue the manipulated stream
- **UI shows:** Temporal score increases
- Risk state: WATCH → ELEVATED

### Step 4: Synthetic Voice (2:30–3:30)
- Play controlled synthetic voice through Browser B's microphone
- **UI shows:** Audio anomaly score increases
- Cross-modal contradiction detected

### Step 5: A/V Inconsistency (3:30–4:00)
- A/V sync score drops
- **UI shows:** Multiple modalities flagged
- Risk state: ELEVATED → HIGH

### Step 6: View Evidence (4:00–4:30)
- Click **VIEW EVIDENCE** on the suspicious event
- Show: heatmap, audio evidence, A/V sync, stability result, model agreement

### Step 7: Forensic Report (4:30–5:00)
- Open forensic report
- Show all evidence with model versions
- Verify audit chain integrity

## Important Notes

- All synthetic media used in the demo must be from **consenting teammates**
- The demo shows `CONTROLLED SYNTHETIC MEDIA TEST` banner when `DEMO_MODE=true`
- The system provides **decision support**, not absolute verdicts
