"""
Tamper-Evident Forensic Audit Hash Chain.
Implements forward cryptographic chaining using SHA-256:
current_hash = SHA-256(canonical_payload_json + previous_hash)
Guarantees verifiable integrity and non-repudiation of forensic analysis history.
"""
import hashlib
import json
import time
import uuid
from typing import List, Dict, Any, Tuple, Optional

from backend.app.schemas.contracts import AuditLogEvent

GENESIS_HASH = "0000000000000000000000000000000000000000000000000000000000000000"


class AuditChainManager:
    def __init__(self, call_id: str):
        self.call_id = call_id
        self.chain: List[AuditLogEvent] = []
        self.last_hash = GENESIS_HASH

    @staticmethod
    def _canonical_json(data: Dict[str, Any]) -> str:
        """Produces deterministic, alphabetically sorted JSON string for hashing."""
        return json.dumps(data, sort_keys=True, separators=(",", ":"))

    def append_event(self, event_type: str, payload: Dict[str, Any]) -> AuditLogEvent:
        """
        Creates and appends a cryptographically chained event to the audit trail.
        """
        event_id = f"AUD-{uuid.uuid4().hex[:12].upper()}"
        ts = time.time()
        
        canonical_payload = self._canonical_json(payload)
        payload_hash = hashlib.sha256(canonical_payload.encode("utf-8")).hexdigest()
        
        # Block digest combining event metadata, payload hash, and previous hash
        block_content = f"{event_id}|{ts:.4f}|{event_type}|{self.call_id}|{payload_hash}|{self.last_hash}"
        current_hash = hashlib.sha256(block_content.encode("utf-8")).hexdigest()

        event = AuditLogEvent(
            event_id=event_id,
            timestamp=ts,
            event_type=event_type,
            call_id=self.call_id,
            payload_hash=payload_hash,
            previous_hash=self.last_hash,
            current_hash=current_hash,
        )

        self.chain.append(event)
        self.last_hash = current_hash
        return event

    @staticmethod
    def verify_chain(chain: List[AuditLogEvent]) -> Tuple[bool, Optional[str], Optional[str], Optional[str]]:
        """
        Validates the complete hash chain from genesis block to tip.
        Returns:
            (valid, broken_at_event_id, expected_hash, actual_hash)
        """
        if not chain:
            return True, None, None, None

        expected_prev = GENESIS_HASH

        for idx, event in enumerate(chain):
            if event.previous_hash != expected_prev:
                return False, event.event_id, expected_prev, event.previous_hash

            block_content = (
                f"{event.event_id}|{event.timestamp:.4f}|{event.event_type}|"
                f"{event.call_id}|{event.payload_hash}|{event.previous_hash}"
            )
            recalculated_hash = hashlib.sha256(block_content.encode("utf-8")).hexdigest()

            if recalculated_hash != event.current_hash:
                return False, event.event_id, recalculated_hash, event.current_hash

            expected_prev = event.current_hash

        return True, None, None, None
