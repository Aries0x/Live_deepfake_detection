# Privacy — Media Integrity / SecureCall

## Data Classification

### LIVE ANALYSIS (Ephemeral)
- Video frames captured for real-time analysis
- Audio chunks captured for real-time analysis
- Processing results during active call
- Rolling buffer of recent frames (configurable size)

### STORED EVIDENCE (Persistent)
- Suspicious event segments (when threshold crossed)
- Forensic reports
- Audit log entries
- Media DNA fingerprints
- Analysis job results

## Retention Policy

Configurable via `RETENTION_MODE`:
- `ephemeral` — Live data discarded after call ends, only audit log and reports retained
- `24h` — Evidence retained for 24 hours, then auto-deleted
- `7d` — Evidence retained for 7 days
- `permanent` — Evidence retained indefinitely (requires explicit opt-in)

## Data Minimization

- Only face crops are stored, not full frames (when configured)
- Audio is not stored by default during live analysis
- Only aggregate scores stored, not raw model internals
- Evidence segments captured only when suspicion threshold is crossed

## User Notice

The UI displays clear notice that:
- Live call media is processed for integrity analysis
- Processing occurs on the local/configured server
- What data retention policy is active

## Face Data

- Face embeddings are used only for identity consistency checks
- Embeddings are not shared externally
- Reference embeddings can be deleted by the user
- ArcFace is an optional feature (disabled by default)

## Consent

- Demo mode requires consenting participants
- All synthetic media tests use clearly labeled controlled inputs
- No covert analysis — participants are informed

## Data Access

- Analysis results accessible only to authorized users
- Audit log provides accountability for all data access
- No third-party data sharing without explicit configuration
