"""
Call Session Manager and WebRTC Signaling Coordination Service.
Maintains active in-memory call states, timeline history, and forensic audit chains.
"""
import time
import uuid
from typing import Dict, List, Optional, Any
from backend.app.schemas.contracts import (
    RiskUpdate,
    CrossModalEvent,
    AuditLogEvent,
)
from audit.hash_chain import AuditChainManager
from reports.generator import ForensicReportGenerator


class ActiveCall:
    def __init__(self, call_id: str, room_id: str, title: str):
        self.call_id = call_id
        self.room_id = room_id
        self.title = title
        self.created_at = time.time()
        self.status = "active"
        
        # Signaling peers (WebSocket connections)
        self.peers: Dict[str, Any] = {}
        
        # Timeline and Evidence
        self.timeline: List[RiskUpdate] = []
        self.events: List[CrossModalEvent] = []
        self.audit_chain = AuditChainManager(call_id)
        
        # Record genesis audit event
        self.audit_chain.append_event(
            "CALL_CREATED",
            {"call_id": call_id, "room_id": room_id, "title": title}
        )

    def record_risk_update(self, update: RiskUpdate):
        self.timeline.append(update)
        if update.active_event is not None:
            self.events.append(update.active_event)
            # Log anomaly event to tamper-evident audit chain
            self.audit_chain.append_event(
                "ANOMALY_DETECTED",
                {
                    "event_id": update.active_event.event_id,
                    "severity": update.active_event.severity,
                    "signals": update.active_event.signals,
                    "risk_score": update.calibrated_risk_score,
                }
            )

        # Log state escalation if elevated or high
        if update.risk_state in ["ELEVATED", "HIGH"]:
            self.audit_chain.append_event(
                "RISK_ESCALATED",
                {
                    "risk_state": update.risk_state,
                    "calibrated_risk": update.calibrated_risk_score,
                    "timestamp": update.timestamp,
                }
            )


class CallManager:
    _instance: Optional["CallManager"] = None

    def __init__(self):
        self.calls: Dict[str, ActiveCall] = {}
        self.room_to_call: Dict[str, str] = {}

    @classmethod
    def get_instance(cls) -> "CallManager":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def create_call(self, room_id: Optional[str] = None, title: Optional[str] = None) -> ActiveCall:
        if room_id and room_id in self.room_to_call:
            existing_id = self.room_to_call[room_id]
            existing = self.calls.get(existing_id)
            if existing and existing.status == "active":
                return existing

        call_id = f"CALL-{uuid.uuid4().hex[:8].upper()}"
        r_id = room_id or f"room-{uuid.uuid4().hex[:6]}"
        t = title or "Live Verification Call"

        call = ActiveCall(call_id=call_id, room_id=r_id, title=t)
        self.calls[call_id] = call
        self.room_to_call[r_id] = call_id
        self.room_to_call[r_id.upper()] = call_id
        self.room_to_call[f"CALL-{r_id.upper()}"] = call_id
        self.calls[f"CALL-{r_id.upper()}"] = call
        return call

    def get_call(self, call_id: str) -> Optional[ActiveCall]:
        if not call_id:
            return None
        call = self.calls.get(call_id)
        if call:
            return call
        if call_id in self.room_to_call:
            return self.calls.get(self.room_to_call[call_id])
        if call_id.upper() in self.room_to_call:
            return self.calls.get(self.room_to_call[call_id.upper()])
        stripped = call_id.replace("CALL-", "").strip()
        if stripped in self.room_to_call:
            return self.calls.get(self.room_to_call[stripped])
        if stripped.upper() in self.room_to_call:
            return self.calls.get(self.room_to_call[stripped.upper()])
        for c in self.calls.values():
            if c.room_id.upper() == call_id.upper() or f"CALL-{c.room_id.upper()}" == call_id.upper():
                return c
        return None

    def get_call_by_room(self, room_id: str) -> Optional[ActiveCall]:
        return self.get_call(room_id)
