"""
Auth Models, In-Memory User Store, and Password Utilities.
Implements bcrypt password hashing, seed data generation, and court case assignments.
"""
import time
import uuid
import bcrypt
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field
from backend.auth.permissions import Role

# Standard Base32 TOTP secret for demo accounts
DEMO_TOTP_SECRET = "JBSWY3DPEHPK3PXP"


class User(BaseModel):
    id: str
    identifier: str  # Email or phone number
    name: str
    role: Role
    hashed_password: Optional[str] = None
    totp_secret: Optional[str] = None
    court_id: Optional[str] = None
    assigned_cases: List[str] = Field(default_factory=list)
    consent_given: bool = False
    is_active: bool = True
    failed_attempts: int = 0
    locked_until: Optional[float] = None
    created_at: float = Field(default_factory=time.time)


class CourtCase(BaseModel):
    case_id: str
    title: str
    description: str
    court_id: str
    assigned_officer_id: Optional[str] = None
    status: str = "open"  # open, pending_approval, approved, closed
    evidence_count: int = 0
    created_at: float = Field(default_factory=time.time)


def hash_password(password: str) -> str:
    """Hash password using bcrypt."""
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against bcrypt hash."""
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
    except Exception:
        return False


class UserStore:
    """
    In-Memory User and Case Store with Seed Data.
    Pre-configured with hackathon demo accounts.
    """
    _instance: Optional["UserStore"] = None

    def __init__(self):
        self.users: Dict[str, User] = {}  # keyed by user_id
        self.users_by_identifier: Dict[str, str] = {}  # identifier -> user_id
        self.cases: Dict[str, CourtCase] = {}  # case_id -> CourtCase
        self._seed_data()

    @classmethod
    def get_instance(cls) -> "UserStore":
        if cls._instance is None:
            cls._instance = UserStore()
        return cls._instance

    def _seed_data(self):
        demo_password_hash = hash_password("Demo@1234")

        # 1. Citizen Demo User
        citizen = User(
            id="usr_citizen_001",
            identifier="citizen@demo.com",
            name="Alex Citizen",
            role=Role.CITIZEN,
            consent_given=True,
        )
        self._add_user(citizen)

        # 2. Forensic Officer Demo User
        officer = User(
            id="usr_officer_001",
            identifier="officer@court.demo",
            name="Det. Sarah Jenkins, Forensic Specialist",
            role=Role.FORENSIC_OFFICER,
            hashed_password=demo_password_hash,
            totp_secret=DEMO_TOTP_SECRET,
            court_id="court-central-01",
            assigned_cases=["CASE-2026-001", "CASE-2026-002"],
        )
        self._add_user(officer)

        # 3. Judge Demo User
        judge = User(
            id="usr_judge_001",
            identifier="judge@court.demo",
            name="Hon. Michael Thorne",
            role=Role.JUDGE,
            hashed_password=demo_password_hash,
            totp_secret=DEMO_TOTP_SECRET,
            court_id="court-central-01",
            assigned_cases=["CASE-2026-001", "CASE-2026-002"],
        )
        self._add_user(judge)

        # 4. Admin Demo User
        admin = User(
            id="usr_admin_001",
            identifier="admin@securecall.demo",
            name="System Administrator",
            role=Role.ADMIN,
            hashed_password=demo_password_hash,
            totp_secret=DEMO_TOTP_SECRET,
        )
        self._add_user(admin)

        # Seed Court Cases
        case1 = CourtCase(
            case_id="CASE-2026-001",
            title="State v. Vance (Neural Voice Cloning Extortion)",
            description="Alleged voice synthesized ransom request targeting financial officer.",
            court_id="court-central-01",
            assigned_officer_id="usr_officer_001",
            status="pending_approval",
            evidence_count=4,
        )
        case2 = CourtCase(
            case_id="CASE-2026-002",
            title="Commercial Fraud v. Apex Capital (Deepfake Video Conference)",
            description="Real-time face-swap interview used in fraudulent authorization of funds.",
            court_id="court-central-01",
            assigned_officer_id="usr_officer_001",
            status="open",
            evidence_count=7,
        )
        self.cases[case1.case_id] = case1
        self.cases[case2.case_id] = case2

    def _add_user(self, user: User):
        self.users[user.id] = user
        self.users_by_identifier[user.identifier.lower().strip()] = user.id

    def get_user_by_id(self, user_id: str) -> Optional[User]:
        return self.users.get(user_id)

    def get_user_by_identifier(self, identifier: str) -> Optional[User]:
        uid = self.users_by_identifier.get(identifier.lower().strip())
        if uid:
            return self.users.get(uid)
        return None

    def get_by_email(self, email: str) -> Optional[User]:
        return self.get_user_by_identifier(email)

    def create_citizen(self, identifier: str, name: str, consent: bool) -> User:
        user_id = f"usr_cit_{uuid.uuid4().hex[:8]}"
        user = User(
            id=user_id,
            identifier=identifier.lower().strip(),
            name=name,
            role=Role.CITIZEN,
            consent_given=consent,
        )
        self._add_user(user)
        return user

    def record_failed_attempt(self, user: User) -> bool:
        """
        Increments failed attempt count. Locks account for 5 minutes if >= 5 attempts.
        Returns True if account is now locked.
        """
        user.failed_attempts += 1
        if user.failed_attempts >= 5:
            user.locked_until = time.time() + 300  # 5 minutes lockout
            return True
        return False

    def reset_failed_attempts(self, user: User):
        user.failed_attempts = 0
        user.locked_until = None

    def is_locked(self, user: User) -> bool:
        if user.locked_until and time.time() < user.locked_until:
            return True
        if user.locked_until and time.time() >= user.locked_until:
            # Lock expired
            self.reset_failed_attempts(user)
        return False
