"""
Security Audit Logger using SHA-256 Tamper-Evident Hash Chain.
Guarantees cryptographic forward-chaining for all authentication, authorization,
evidence access, and administrative actions.
"""
from typing import Dict, Any, Optional, List, Tuple
from audit.hash_chain import AuditChainManager, AuditLogEvent
from backend.app.logging_config import get_logger

logger = get_logger("security_audit")


class SecurityAuditLogger:
    _instance: Optional["SecurityAuditLogger"] = None

    def __init__(self):
        self.chain_manager = AuditChainManager(call_id="SYSTEM-SECURITY")

    @classmethod
    def get_instance(cls) -> "SecurityAuditLogger":
        if cls._instance is None:
            cls._instance = SecurityAuditLogger()
        return cls._instance

    def log_event(self, event_type: str, payload: Dict[str, Any]) -> AuditLogEvent:
        """
        Appends an event to the global security hash chain.
        """
        event = self.chain_manager.append_event(event_type=event_type, payload=payload)
        logger.info(
            "Audit event logged to hash chain",
            event_id=event.event_id,
            event_type=event_type,
            current_hash=event.current_hash[:16] + "...",
        )
        return event

    def get_chain(self) -> List[AuditLogEvent]:
        """Returns the full chronological audit chain."""
        return self.chain_manager.chain

    def verify_integrity(self) -> Tuple[bool, Optional[str], Optional[str], Optional[str]]:
        """
        Verifies the cryptographic integrity of the audit hash chain from genesis to tip.
        """
        return AuditChainManager.verify_chain(self.chain_manager.chain)
