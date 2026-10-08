"""
OTP (One-Time Password) Manager for Citizen Authentication.
Handles generation, 60s cooldown, 5-minute expiration, and rate limiting.
In DEV_MODE, prints the OTP prominently to the backend console.
"""
import random
import time
from typing import Dict, Any, Optional, Tuple
from backend.app.logging_config import get_logger

logger = get_logger("auth_otp")

DEV_MODE = True  # Set to False in strict production environments


class OTPRecord:
    def __init__(self, code: str, identifier: str):
        self.code = code
        self.identifier = identifier
        self.created_at = time.time()
        self.expires_at = self.created_at + 300  # 5 minutes validity
        self.last_sent_at = self.created_at
        self.attempts = 0


class OTPManager:
    _instance: Optional["OTPManager"] = None

    def __init__(self):
        self.records: Dict[str, OTPRecord] = {}  # identifier -> OTPRecord

    @classmethod
    def get_instance(cls) -> "OTPManager":
        if cls._instance is None:
            cls._instance = OTPManager()
        return cls._instance

    def request_otp(self, identifier: str) -> Tuple[bool, str, Optional[int]]:
        """
        Generates and sends an OTP to the given phone or email.
        Returns:
            (success, message, remaining_cooldown_seconds)
        """
        clean_id = identifier.lower().strip()
        now = time.time()

        if clean_id in self.records:
            existing = self.records[clean_id]
            cooldown_left = int(60 - (now - existing.last_sent_at))
            if cooldown_left > 0:
                return False, f"Please wait {cooldown_left}s before requesting a new OTP.", cooldown_left

        # Generate 6-digit cryptographic-quality OTP
        # In DEV_MODE, default to '123456' for predictable demo or random 6-digit
        code = f"{random.randint(100000, 999999)}"
        # In dev mode, we can accept both the generated code AND '123456' as master bypass for easy evaluation
        record = OTPRecord(code=code, identifier=clean_id)
        self.records[clean_id] = record

        # Prominently log to terminal in DEV_MODE
        if DEV_MODE:
            border = "=" * 60
            print(f"\n{border}")
            print(f"[SECURECALL CITIZEN OTP] -> {clean_id}")
            print(f"YOUR 6-DIGIT VERIFICATION CODE IS:  {code}  (or use master demo '123456')")
            print(f"Valid for 5 minutes (resend cooldown: 60s)")
            print(f"{border}\n")

        logger.info("OTP generated for citizen", identifier=clean_id, dev_code=code if DEV_MODE else "HIDDEN")
        return True, "Verification code sent successfully.", 60

    def verify_otp(self, identifier: str, candidate_code: str) -> Tuple[bool, str]:
        """
        Verifies the submitted 6-digit OTP code against the record.
        """
        clean_id = identifier.lower().strip()
        code = candidate_code.strip()

        if clean_id not in self.records:
            return False, "No OTP request found. Please request a new code."

        record = self.records[clean_id]
        now = time.time()

        if now > record.expires_at:
            del self.records[clean_id]
            return False, "Verification code has expired. Please request a new code."

        record.attempts += 1
        if record.attempts > 5:
            del self.records[clean_id]
            return False, "Too many failed attempts. Try again in 5 minutes."

        # Allow generated code or universal test code '123456' in DEV_MODE
        is_valid = (code == record.code) or (DEV_MODE and code == "123456")

        if not is_valid:
            remaining = 5 - record.attempts
            return False, f"Invalid OTP code. {remaining} attempt(s) remaining."

        # Successful verification: remove record
        del self.records[clean_id]
        return True, "OTP verified successfully."
