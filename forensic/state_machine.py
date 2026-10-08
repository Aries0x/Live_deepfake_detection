"""
Continuous Risk State Machine.
Controls progressive escalation and recovery across risk states:
NORMAL -> WATCH -> ELEVATED -> HIGH -> (recovery) -> NORMAL.
Prevents single-frame false spikes via temporal persistence requirements.
"""
from typing import Optional
from backend.app.config import settings
from backend.app.schemas.contracts import RiskState


class RiskStateMachine:
    def __init__(self):
        self.state: RiskState = RiskState.NORMAL
        self.consecutive_suspicious_windows: int = 0
        self.consecutive_normal_windows: int = 0
        self.time_in_high: float = 0.0
        
        self.min_suspicious = settings.MIN_SUSPICIOUS_WINDOWS
        self.watch_thresh = settings.WATCH_THRESHOLD
        self.elevated_thresh = settings.ELEVATED_THRESHOLD
        self.high_thresh = settings.HIGH_RISK_THRESHOLD

    def update(
        self,
        calibrated_risk: float,
        multimodal_count: int = 1,
        dt_seconds: float = 0.2,
    ) -> RiskState:
        """
        Step the state machine forward given the latest calibrated risk score.
        """
        if calibrated_risk >= self.elevated_thresh:
            self.consecutive_suspicious_windows += 1
            self.consecutive_normal_windows = 0
        elif calibrated_risk <= self.watch_thresh:
            self.consecutive_normal_windows += 1
            self.consecutive_suspicious_windows = max(0, self.consecutive_suspicious_windows - 1)
        else:
            # Ambiguous / Watch zone
            pass

        # Escalation Logic
        if self.state == RiskState.NORMAL:
            if calibrated_risk >= self.watch_thresh:
                self.state = RiskState.WATCH

        elif self.state == RiskState.WATCH:
            if self.consecutive_suspicious_windows >= self.min_suspicious:
                self.state = RiskState.ELEVATED
            elif self.consecutive_normal_windows >= 4:
                self.state = RiskState.NORMAL

        elif self.state == RiskState.ELEVATED:
            # Require multimodal agreement or severe persistent risk to trigger HIGH
            if (
                calibrated_risk >= self.high_thresh
                and self.consecutive_suspicious_windows >= (self.min_suspicious + 2)
                and multimodal_count >= settings.MIN_MULTIMODAL_AGREEMENT
            ):
                self.state = RiskState.HIGH
                self.time_in_high = 0.0
            elif self.consecutive_normal_windows >= 4:
                self.state = RiskState.WATCH

        elif self.state == RiskState.HIGH:
            self.time_in_high += dt_seconds
            # Recovery path: requires sustained normal observations
            if self.consecutive_normal_windows >= 6 and self.time_in_high >= settings.HIGH_RISK_DURATION:
                self.state = RiskState.ELEVATED
                self.time_in_high = 0.0

        return self.state
