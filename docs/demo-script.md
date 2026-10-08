# Demo Script — Media Integrity / SecureCall

## 5-Minute Hackathon Demonstration

### Pre-Demo Setup
1. Ensure `DEMO_MODE=true` in `.env`
2. All services running: PostgreSQL, Redis, Backend, Frontend
3. Two browsers/tabs ready
4. Controlled synthetic media test inputs prepared (consenting teammates only)

---

### STEP 1 — Normal Call (0:00–1:00)
**Action:** Start a normal WebRTC call between two participants.

**UI State:**
- Risk indicator: 🟢 **LOW RISK**
- All scores near baseline
- Timeline shows flat, low-risk trajectory

**Talking Point:** "We've established a normal video call. The system is continuously analyzing the remote participant's video and audio in real time."

---

### STEP 2 — Face-Swap Introduction (1:00–2:00)
**Action:** Switch Browser B's camera input to a controlled face-swap stream.

**UI State:**
- Visual anomaly score rises (e.g., 0.12 → 0.72)
- Risk state: NORMAL → 🟡 **WATCH**
- Timeline shows upward trend

**Talking Point:** "A face-swap has been introduced. The visual model detects manipulation artifacts in the face region."

---

### STEP 3 — Temporal Evidence Builds (2:00–2:30)
**Action:** Continue the face-swap stream for persistent evidence.

**UI State:**
- Temporal score increases
- Risk state: WATCH → 🟠 **ELEVATED MANIPULATION EVIDENCE**

**Talking Point:** "The system requires persistent evidence across multiple frames before escalating — it doesn't trigger from a single frame."

---

### STEP 4 — Synthetic Voice (2:30–3:30)
**Action:** Introduce controlled synthetic voice through Browser B.

**UI State:**
- Audio anomaly score rises
- Cross-modal contradiction detected (visual + audio both anomalous)
- Risk: remains **ELEVATED** or transitions to **HIGH**

**Talking Point:** "Now both visual and audio modalities show anomalies, and the cross-modal engine detects agreement between them."

---

### STEP 5 — A/V Desynchronization (3:30–4:00)
**Action:** Continue with synthetic media showing poor lip sync.

**UI State:**
- A/V sync score drops
- Multiple modalities now flagged
- Risk state: 🔴 **HIGH MANIPULATION EVIDENCE**

**Talking Point:** "Audio-video synchronization is poor, providing additional independent evidence. The system now reports HIGH manipulation evidence."

---

### STEP 6 — Evidence Review (4:00–4:30)
**Action:** Click "VIEW EVIDENCE" on the suspicious event in the timeline.

**Show:**
- Suspicious timestamp range
- Representative frame with heatmap overlay
- Audio evidence markers
- A/V synchronization chart
- Identity comparison (if enabled)
- Evidence stability: HIGH
- Model agreement status

**Talking Point:** "The evidence panel shows exactly what the models detected, when they detected it, and how stable the evidence is across transformations."

---

### STEP 7 — Forensic Report (4:30–4:45)
**Action:** Open the forensic report.

**Show:**
- Media SHA-256 hash
- All model versions
- Raw and calibrated scores
- Suspicious intervals
- Human-readable explanation
- Limitations disclaimer

**Talking Point:** "A complete forensic report with tamper-evident audit trail is generated automatically."

---

### STEP 8 — Audit Verification (4:45–5:00)
**Action:** Verify the audit chain.

**Show:**
- All events in hash chain
- Verification result: VALID
- Hash chain integrity confirmed

**Talking Point:** "Every analysis event is recorded in a tamper-evident hash chain, ensuring the forensic record cannot be altered."

---

## Key Messages

1. **Innovation:** "We correlate and stress-test multimodal forensic evidence during a live communication."
2. **Not absolute:** "The system provides decision support with uncertainty quantification — never claims 100% real or fake."
3. **Differentiators:**
   - Continuous trust trajectory
   - Cross-modal contradiction detection
   - Evidence stability testing
   - Media DNA fingerprinting
   - Tamper-evident forensic audit trail
