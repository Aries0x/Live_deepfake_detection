"""
FastAPI Authentication & RBAC Routes for SecureCall.
Implements Citizen OTP flow, Court/Admin password + 2FA TOTP flow,
session cookie lifecycle, step-up reauthentication, and audit hash chain verification.
"""
import time
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, Response, Request, Depends, status
from pydantic import BaseModel, Field

from backend.auth.models import (
    UserStore,
    Role,
    verify_password,
    CourtCase,
    DEMO_TOTP_SECRET,
)
from backend.auth.otp import OTPManager, DEV_MODE
from backend.auth.totp import (
    create_pending_2fa_token,
    decode_pending_2fa_token,
    verify_totp_code,
    get_current_totp_code,
)
from backend.auth.dependencies import (
    create_session_jwt,
    get_current_user,
    get_token_from_request,
    require_permission,
    COOKIE_NAME,
)
from backend.auth.permissions import Permission
from backend.auth.security_audit import SecurityAuditLogger
from backend.app.logging_config import get_logger

logger = get_logger("auth_routes")
router = APIRouter()

# -----------------------------------------------------------------------------
# Request & Response Schemas
# -----------------------------------------------------------------------------
class CitizenOtpRequest(BaseModel):
    identifier: str = Field(..., description="Phone number or email address")


class CitizenVerifyRequest(BaseModel):
    identifier: str
    otp: str
    name: Optional[str] = None
    consent: Optional[bool] = False


class CourtLoginRequest(BaseModel):
    email: str
    password: str
    role: str = Field(..., description="'forensic_officer' or 'judge'")


class UnifiedLoginRequest(BaseModel):
    identifier: str = Field(..., description="Email or phone number")
    password: Optional[str] = Field(None, description="Account password")
    otp: Optional[str] = Field(None, description="Optional OTP code")
    consent: Optional[bool] = False


class AdminLoginRequest(BaseModel):
    email: str
    password: str


class Verify2FARequest(BaseModel):
    pending_token: str
    totp_code: str


class ReauthTotpRequest(BaseModel):
    totp_code: str
    action: str = Field(default="bulk.approve_report", description="Action being confirmed")


class CreateCaseRequest(BaseModel):
    case_id: Optional[str] = None
    title: str
    description: str
    court_id: Optional[str] = "court-central-01"


class UpdateThresholdsRequest(BaseModel):
    risk_threshold: float = Field(0.65, ge=0.0, le=1.0)
    face_weight: float = Field(0.50, ge=0.0, le=1.0)
    audio_weight: float = Field(0.30, ge=0.0, le=1.0)
    temporal_weight: float = Field(0.20, ge=0.0, le=1.0)
    totp_code: str


SYSTEM_THRESHOLDS = {
    "risk_threshold": 0.65,
    "face_weight": 0.50,
    "audio_weight": 0.30,
    "temporal_weight": 0.20,
}


# Helper for setting secure session cookie
def set_auth_cookie(response: Response, token: str, role: str):
    max_age = 8 * 3600 if role == Role.CITIZEN.value else 30 * 60
    # In development on localhost (http), secure=False allows cookie to be saved by browser
    response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        max_age=max_age,
        expires=max_age,
        httponly=True,
        samesite="lax",
        secure=False,
        path="/",
    )


# -----------------------------------------------------------------------------
# 0. Unified Single Login & Step-Up 2FA Endpoints
# -----------------------------------------------------------------------------
@router.post("/auth/login")
async def unified_login(req: UnifiedLoginRequest, response: Response):
    """
    Unified Single Login:
    The user enters credentials without needing to pick a role.
    The system verifies the account and role configured by admin:
      - Citizen: authenticates via password or OTP, issues session cookie, returns role 'citizen'.
      - Forensic Officer / Judge / Admin: verifies password, returns short-lived pending_2fa token for step 2.
    """
    user_store = UserStore.get_instance()
    audit = SecurityAuditLogger.get_instance()

    identifier = req.identifier.strip()
    user = user_store.get_user_by_identifier(identifier)

    # If user doesn't exist yet, allow citizen signup if OTP is provided or default to citizen in dev mode
    if not user:
        if req.otp:
            otp_mgr = OTPManager.get_instance()
            valid, msg = otp_mgr.verify_otp(identifier, req.otp)
            if not valid:
                audit.log_event("AUTH_LOGIN_FAILED", {"identifier": identifier, "reason": msg})
                raise HTTPException(status_code=400, detail=msg)
            user = user_store.create_citizen(identifier, name=f"Citizen {identifier[-4:]}", consent=bool(req.consent))
        elif DEV_MODE and ("citizen" in identifier or "@demo" in identifier):
            user = user_store.create_citizen(identifier, name="Demo Citizen", consent=True)
        else:
            audit.log_event("AUTH_LOGIN_FAILED", {"identifier": identifier, "reason": "User not found"})
            raise HTTPException(status_code=401, detail="Invalid email or password.")

    # Check lock status
    if user_store.is_locked(user):
        audit.log_event("AUTH_ACCOUNT_LOCKED", {"user_id": user.id, "identifier": identifier})
        raise HTTPException(status_code=429, detail="Too many attempts. Account locked. Try again in 5 minutes.")

    # 1. Citizen Role
    if user.role == Role.CITIZEN:
        # Check OTP if provided
        if req.otp:
            otp_mgr = OTPManager.get_instance()
            valid, msg = otp_mgr.verify_otp(identifier, req.otp)
            if not valid:
                audit.log_event("AUTH_LOGIN_FAILED", {"identifier": identifier, "reason": msg})
                raise HTTPException(status_code=400, detail=msg)
        elif req.password:
            if user.hashed_password:
                if not verify_password(req.password, user.hashed_password):
                    raise HTTPException(status_code=401, detail="Invalid password.")
            elif req.password != "Demo@1234":
                raise HTTPException(status_code=401, detail="Invalid password.")
        else:
            raise HTTPException(status_code=400, detail="Please provide a password or OTP code.")

        session_token = create_session_jwt(user)
        set_auth_cookie(response, session_token, user.role.value)
        audit.log_event("AUTH_LOGIN_SUCCESS", {"user_id": user.id, "role": user.role.value})

        return {
            "success": True,
            "requires_2fa": False,
            "role": user.role.value,
            "user_id": user.id,
            "name": user.name,
            "token": session_token,
        }

    # 2. Privileged Roles (Forensic Officer, Judge, Admin) -> Password + mandatory 2FA
    if not req.password:
        raise HTTPException(status_code=400, detail="Password required for court/admin credentials.")

    if not verify_password(req.password, user.hashed_password or ""):
        is_locked = user_store.record_failed_attempt(user)
        audit.log_event("AUTH_LOGIN_FAILED", {"user_id": user.id, "reason": "Incorrect password"})
        if is_locked:
            raise HTTPException(status_code=429, detail="Too many attempts. Account locked. Try again in 5 minutes.")
        remaining = 5 - user.failed_attempts
        raise HTTPException(status_code=401, detail=f"Invalid password. {remaining} attempt(s) remaining.")

    user_store.reset_failed_attempts(user)
    pending_token = create_pending_2fa_token(user.id, user.role.value)
    active_totp = get_current_totp_code(user.totp_secret or DEMO_TOTP_SECRET) if DEV_MODE else None

    return {
        "success": True,
        "requires_2fa": True,
        "pending_token": pending_token,
        "role": user.role.value,
        "email": user.identifier,
        "dev_totp_code": active_totp,
        "message": f"Verified credentials for {user.role.value.replace('_', ' ').title()}. Enter 6-digit TOTP.",
    }


@router.post("/auth/verify-2fa")
async def unified_verify_2fa(req: Verify2FARequest, response: Response):
    """
    Step 2 of unified login for court and admin accounts.
    """
    user_store = UserStore.get_instance()
    audit = SecurityAuditLogger.get_instance()

    payload = decode_pending_2fa_token(req.pending_token)
    if not payload:
        raise HTTPException(status_code=401, detail="Session expired or invalid pending token.")

    user = user_store.get_user_by_id(payload["sub"])
    if not user:
        raise HTTPException(status_code=404, detail="User account not found.")

    if not verify_totp_code(user.totp_secret or DEMO_TOTP_SECRET, req.totp_code):
        audit.log_event("AUTH_2FA_FAILED", {"user_id": user.id, "role": user.role.value})
        raise HTTPException(status_code=400, detail="Invalid 2FA code.")

    session_token = create_session_jwt(user)
    set_auth_cookie(response, session_token, user.role.value)

    audit.log_event("AUTH_LOGIN_SUCCESS", {"user_id": user.id, "role": user.role.value, "method": "unified_2fa"})

    return {
        "success": True,
        "user_id": user.id,
        "name": user.name,
        "role": user.role.value,
        "court_id": user.court_id,
        "assigned_cases": user.assigned_cases,
        "token": session_token,
    }


# -----------------------------------------------------------------------------
# 1. Citizen Authentication Endpoints (OTP)
# -----------------------------------------------------------------------------
@router.post("/auth/citizen/request-otp")
async def citizen_request_otp(req: CitizenOtpRequest):
    """
    Step 1: Citizen enters phone number or email to request a 6-digit OTP.
    In DEV_MODE, the OTP is printed to the backend terminal for evaluation ease.
    """
    otp_mgr = OTPManager.get_instance()
    success, msg, cooldown = otp_mgr.request_otp(req.identifier)
    if not success:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=msg)

    # In dev mode, return demo hint so the user UI can provide instant feedback
    demo_hint = "123456" if DEV_MODE else None

    return {
        "success": True,
        "message": msg,
        "cooldown_seconds": cooldown,
        "dev_code": demo_hint,
    }


@router.post("/auth/citizen/verify-otp")
async def citizen_verify_otp(req: CitizenVerifyRequest, response: Response):
    """
    Step 2: Citizen submits the 6-digit OTP. If first-time user, creates account with name & consent.
    Issues an 8-hour httpOnly session cookie and logs to audit hash chain.
    """
    otp_mgr = OTPManager.get_instance()
    user_store = UserStore.get_instance()
    audit = SecurityAuditLogger.get_instance()

    valid, msg = otp_mgr.verify_otp(req.identifier, req.otp)
    if not valid:
        audit.log_event(
            event_type="AUTH_LOGIN_FAILED",
            payload={"identifier": req.identifier, "reason": msg, "role": Role.CITIZEN.value},
        )
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=msg)

    user = user_store.get_user_by_identifier(req.identifier)
    is_new = False
    if not user:
        is_new = True
        display_name = req.name.strip() if req.name and req.name.strip() else f"Citizen {req.identifier[-4:]}"
        user = user_store.create_citizen(
            identifier=req.identifier,
            name=display_name,
            consent=bool(req.consent),
        )
    else:
        if req.name and req.name.strip():
            user.name = req.name.strip()
        if req.consent is not None:
            user.consent_given = bool(req.consent)

    session_token = create_session_jwt(user)
    set_auth_cookie(response, session_token, user.role.value)

    audit.log_event(
        event_type="AUTH_LOGIN_SUCCESS",
        payload={
            "user_id": user.id,
            "role": user.role.value,
            "identifier": user.identifier,
            "is_new_user": is_new,
        },
    )

    return {
        "success": True,
        "user_id": user.id,
        "name": user.name,
        "role": user.role.value,
        "is_new_user": is_new,
        "token": session_token,
    }


# -----------------------------------------------------------------------------
# 2. Court Authentication Endpoints (Password + TOTP)
# -----------------------------------------------------------------------------
@router.post("/auth/court/login")
async def court_login(req: CourtLoginRequest):
    """
    Step 1 for Court Users (Forensic Officer / Judge):
    Verifies email, password, and declared role.
    Returns short-lived pending_2fa token for 2FA TOTP verification.
    """
    user_store = UserStore.get_instance()
    audit = SecurityAuditLogger.get_instance()

    user = user_store.get_user_by_identifier(req.email)
    if not user or user.role not in (Role.FORENSIC_OFFICER, Role.JUDGE):
        audit.log_event(
            event_type="AUTH_LOGIN_FAILED",
            payload={"email": req.email, "declared_role": req.role, "reason": "Account not found"},
        )
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password.")

    if user_store.is_locked(user):
        audit.log_event(
            event_type="AUTH_ACCOUNT_LOCKED",
            payload={"email": req.email, "user_id": user.id},
        )
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many attempts. Account locked. Try again in 5 minutes.",
        )

    # Role Mismatch Check (User must not claim Judge if they are Forensic Officer, or vice versa)
    if user.role.value != req.role:
        audit.log_event(
            event_type="AUTH_ROLE_MISMATCH",
            payload={"email": req.email, "declared_role": req.role, "actual_role": user.role.value},
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Role mismatch. Account is registered as '{user.role.value}', not '{req.role}'.",
        )

    if not verify_password(req.password, user.hashed_password or ""):
        is_now_locked = user_store.record_failed_attempt(user)
        audit.log_event(
            event_type="AUTH_LOGIN_FAILED",
            payload={"email": req.email, "user_id": user.id, "reason": "Incorrect password"},
        )
        if is_now_locked:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many attempts. Account locked. Try again in 5 minutes.",
            )
        remaining = 5 - user.failed_attempts
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid password. {remaining} attempt(s) remaining.",
        )

    # Password verified: reset attempt counter and generate pending 2FA token
    user_store.reset_failed_attempts(user)
    pending_token = create_pending_2fa_token(user.id, user.role.value)

    # In dev mode, compute active TOTP code for instant feedback
    active_totp = get_current_totp_code(user.totp_secret or DEMO_TOTP_SECRET) if DEV_MODE else None

    return {
        "success": True,
        "requires_2fa": True,
        "pending_token": pending_token,
        "role": user.role.value,
        "message": "Password verified. Please enter your 6-digit TOTP authenticator code.",
        "dev_totp_code": active_totp,
    }


@router.post("/auth/court/verify-2fa")
async def court_verify_2fa(req: Verify2FARequest, response: Response):
    """
    Step 2 for Court Users:
    Verifies the 6-digit TOTP code against user's secret.
    Issues a 30-minute sliding session cookie and logs to audit hash chain.
    """
    user_store = UserStore.get_instance()
    audit = SecurityAuditLogger.get_instance()

    payload = decode_pending_2fa_token(req.pending_token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session expired or invalid pending token. Please log in again.",
        )

    user = user_store.get_user_by_id(payload["sub"])
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User account not found.")

    if not verify_totp_code(user.totp_secret or DEMO_TOTP_SECRET, req.totp_code):
        audit.log_event(
            event_type="AUTH_2FA_FAILED",
            payload={"user_id": user.id, "role": user.role.value},
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid 2FA code. Please verify the code in your authenticator app.",
        )

    session_token = create_session_jwt(user)
    set_auth_cookie(response, session_token, user.role.value)

    audit.log_event(
        event_type="AUTH_LOGIN_SUCCESS",
        payload={
            "user_id": user.id,
            "role": user.role.value,
            "court_id": user.court_id,
            "method": "password+totp",
        },
    )

    return {
        "success": True,
        "user_id": user.id,
        "name": user.name,
        "role": user.role.value,
        "court_id": user.court_id,
        "assigned_cases": user.assigned_cases,
        "token": session_token,
    }


# -----------------------------------------------------------------------------
# 3. Administrator Authentication Endpoints
# -----------------------------------------------------------------------------
@router.post("/auth/admin/login")
async def admin_login(req: AdminLoginRequest):
    """
    Step 1 for Administrator: Email + Password.
    Returns short-lived pending_2fa token.
    """
    user_store = UserStore.get_instance()
    audit = SecurityAuditLogger.get_instance()

    user = user_store.get_user_by_identifier(req.email)
    if not user or user.role != Role.ADMIN:
        audit.log_event(
            event_type="AUTH_LOGIN_FAILED",
            payload={"email": req.email, "role": "admin", "reason": "Admin account not found"},
        )
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid admin credentials.")

    if user_store.is_locked(user):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many attempts. Account locked. Try again in 5 minutes.",
        )

    if not verify_password(req.password, user.hashed_password or ""):
        is_locked = user_store.record_failed_attempt(user)
        audit.log_event(
            event_type="AUTH_LOGIN_FAILED",
            payload={"email": req.email, "user_id": user.id, "reason": "Incorrect password"},
        )
        if is_locked:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many attempts. Account locked. Try again in 5 minutes.",
            )
        remaining = 5 - user.failed_attempts
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid password. {remaining} attempt(s) remaining.",
        )

    user_store.reset_failed_attempts(user)
    pending_token = create_pending_2fa_token(user.id, user.role.value)
    active_totp = get_current_totp_code(user.totp_secret or DEMO_TOTP_SECRET) if DEV_MODE else None

    return {
        "success": True,
        "requires_2fa": True,
        "pending_token": pending_token,
        "role": Role.ADMIN.value,
        "message": "Admin credentials verified. Enter mandatory 6-digit TOTP.",
        "dev_totp_code": active_totp,
    }


@router.post("/auth/admin/verify-2fa")
async def admin_verify_2fa(req: Verify2FARequest, response: Response):
    """
    Step 2 for Administrator: Verifies TOTP code.
    Issues 30-minute session cookie and logs to audit hash chain.
    """
    user_store = UserStore.get_instance()
    audit = SecurityAuditLogger.get_instance()

    payload = decode_pending_2fa_token(req.pending_token)
    if not payload or payload.get("role") != Role.ADMIN.value:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired admin session token.")

    user = user_store.get_user_by_id(payload["sub"])
    if not user or user.role != Role.ADMIN:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Admin account not found.")

    if not verify_totp_code(user.totp_secret or DEMO_TOTP_SECRET, req.totp_code):
        audit.log_event(
            event_type="AUTH_2FA_FAILED",
            payload={"user_id": user.id, "role": "admin"},
        )
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid admin 2FA code.")

    session_token = create_session_jwt(user)
    set_auth_cookie(response, session_token, user.role.value)

    audit.log_event(
        event_type="AUTH_LOGIN_SUCCESS",
        payload={"user_id": user.id, "role": "admin", "method": "admin_2fa"},
    )

    return {
        "success": True,
        "user_id": user.id,
        "name": user.name,
        "role": user.role.value,
        "token": session_token,
    }


# -----------------------------------------------------------------------------
# 4. Session Introspection, Logout, and Step-Up TOTP Verification
# -----------------------------------------------------------------------------
@router.get("/auth/me")
async def get_me(request: Request, user: Dict[str, Any] = Depends(get_current_user)):
    """Returns currently authenticated user profile, permissions, and scope."""
    token = get_token_from_request(request)
    return {**user, "token": token}


@router.post("/auth/logout")
async def logout(response: Response, user: Dict[str, Any] = Depends(get_current_user)):
    """Clears the session cookie and appends logout event to audit hash chain."""
    response.delete_cookie(key=COOKIE_NAME, path="/")
    audit = SecurityAuditLogger.get_instance()
    audit.log_event(
        event_type="AUTH_LOGOUT",
        payload={"user_id": user.get("user_id"), "role": user.get("role")},
    )
    return {"success": True, "message": "Logged out successfully."}


@router.post("/auth/reauth-totp")
async def reauth_totp(
    req: ReauthTotpRequest,
    user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Mandatory step-up authentication:
    Re-verifies TOTP code before critical actions like 'bulk.approve_report' or 'evidence.edit_or_delete'.
    """
    user_store = UserStore.get_instance()
    audit = SecurityAuditLogger.get_instance()

    user_obj = user_store.get_user_by_id(user.get("user_id", ""))
    if not user_obj:
        raise HTTPException(status_code=404, detail="User account not found.")

    if not verify_totp_code(user_obj.totp_secret or DEMO_TOTP_SECRET, req.totp_code):
        audit.log_event(
            event_type="AUTH_REAUTH_FAILED",
            payload={"user_id": user_obj.id, "action": req.action},
        )
        raise HTTPException(status_code=400, detail="Invalid 2FA code. Authorization denied.")

    audit.log_event(
        event_type="AUTH_REAUTH_SUCCESS",
        payload={"user_id": user_obj.id, "action": req.action},
    )
    return {"success": True, "verified": True, "action": req.action}


# -----------------------------------------------------------------------------
# 5. Court Cases & Evidence Management (Protected by RBAC)
# -----------------------------------------------------------------------------
@router.get("/auth/cases")
async def list_cases(user: Dict[str, Any] = Depends(get_current_user)):
    """
    Lists court cases according to user role:
      - Admin: all cases
      - Judge: cases in own court
      - Forensic Officer: assigned cases
      - Citizen: 403 Forbidden
    """
    user_store = UserStore.get_instance()
    role = user.get("role")

    if role == Role.CITIZEN.value:
        raise HTTPException(status_code=403, detail="Citizens do not have access to court cases.")

    all_cases = list(user_store.cases.values())
    if role == Role.ADMIN.value:
        return [c.model_dump() for c in all_cases]

    if role == Role.JUDGE.value:
        court_id = user.get("court_id")
        return [c.model_dump() for c in all_cases if c.court_id == court_id]

    if role == Role.FORENSIC_OFFICER.value:
        assigned = user.get("assigned_cases") or []
        return [c.model_dump() for c in all_cases if c.case_id in assigned]

    return []


@router.post("/auth/cases")
async def create_case(
    req: CreateCaseRequest,
    user: Dict[str, Any] = Depends(require_permission(Permission.BULK_CREATE_CASE)),
):
    """Creates a new court evidence case (Forensic Officer or Admin)."""
    user_store = UserStore.get_instance()
    audit = SecurityAuditLogger.get_instance()

    case_id = req.case_id or f"CASE-2026-{len(user_store.cases) + 1:03d}"
    new_case = CourtCase(
        case_id=case_id,
        title=req.title,
        description=req.description,
        court_id=req.court_id or user.get("court_id") or "court-central-01",
        assigned_officer_id=user.get("user_id"),
        status="open",
        evidence_count=0,
    )
    user_store.cases[case_id] = new_case

    # Assign to creating officer
    if user.get("role") == Role.FORENSIC_OFFICER.value:
        user_obj = user_store.get_user_by_id(user.get("user_id", ""))
        if user_obj and case_id not in user_obj.assigned_cases:
            user_obj.assigned_cases.append(case_id)

    audit.log_event(
        event_type="CASE_CREATED",
        payload={
            "case_id": case_id,
            "created_by": user.get("user_id"),
            "role": user.get("role"),
            "title": req.title,
        },
    )

    return new_case.model_dump()


@router.post("/auth/cases/{case_id}/approve")
async def approve_case_report(
    case_id: str,
    req: ReauthTotpRequest,
    user: Dict[str, Any] = Depends(require_permission(Permission.BULK_APPROVE_REPORT)),
):
    """
    Approves a court forensic report. Requires Judge role and TOTP step-up confirmation.
    """
    user_store = UserStore.get_instance()
    audit = SecurityAuditLogger.get_instance()

    case = user_store.cases.get(case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found.")

    # Re-verify TOTP
    user_obj = user_store.get_user_by_id(user.get("user_id", ""))
    if not verify_totp_code(user_obj.totp_secret or DEMO_TOTP_SECRET if user_obj else "", req.totp_code):
        raise HTTPException(status_code=400, detail="Invalid 2FA code. Approval rejected.")

    case.status = "approved"

    audit.log_event(
        event_type="REPORT_APPROVED",
        payload={
            "case_id": case_id,
            "approved_by": user.get("user_id"),
            "role": user.get("role"),
            "timestamp": time.time(),
        },
    )

    return {"success": True, "case_id": case_id, "status": "approved", "message": "Forensic report approved and signed."}


# -----------------------------------------------------------------------------
# 6. Tamper-Evident Hash Chain Audit Endpoints
# -----------------------------------------------------------------------------
@router.get("/auth/audit/chain")
async def get_audit_chain(user: Dict[str, Any] = Depends(require_permission(Permission.AUDIT_VERIFY_HASH_CHAIN))):
    """Returns the chronological tamper-evident SHA-256 hash chain."""
    audit = SecurityAuditLogger.get_instance()
    chain = audit.get_chain()
    return {"chain_length": len(chain), "events": [e.model_dump() for e in chain]}


@router.get("/auth/audit/verify")
async def verify_audit_chain(user: Dict[str, Any] = Depends(require_permission(Permission.AUDIT_VERIFY_HASH_CHAIN))):
    """Verifies cryptographic forward-chaining integrity of the audit log."""
    audit = SecurityAuditLogger.get_instance()
    valid, broken_id, exp_hash, act_hash = audit.verify_integrity()
    return {
        "valid": valid,
        "chain_length": len(audit.get_chain()),
        "broken_at_event_id": broken_id,
        "expected_hash": exp_hash,
        "actual_hash": act_hash,
    }


# -----------------------------------------------------------------------------
# 7. Administrator Management Endpoints
# -----------------------------------------------------------------------------
@router.get("/auth/admin/users")
async def admin_list_users(user: Dict[str, Any] = Depends(require_permission(Permission.ADMIN_MANAGE_ACCOUNTS))):
    """Lists all user accounts for admin review."""
    user_store = UserStore.get_instance()
    results = []
    for u in user_store.users.values():
        results.append({
            "id": u.id,
            "name": u.name,
            "identifier": u.identifier,
            "role": u.role.value,
            "court_id": u.court_id,
            "assigned_cases": u.assigned_cases,
            "failed_attempts": u.failed_attempts,
            "is_locked": user_store.is_locked(u),
            "consent_given": u.consent_given,
        })
    return results


@router.get("/auth/admin/thresholds")
async def admin_get_thresholds(user: Dict[str, Any] = Depends(require_permission(Permission.ADMIN_CHANGE_THRESHOLDS))):
    """Returns current detection sensitivity thresholds."""
    return SYSTEM_THRESHOLDS


@router.post("/auth/admin/thresholds")
async def admin_update_thresholds(
    req: UpdateThresholdsRequest,
    user: Dict[str, Any] = Depends(require_permission(Permission.ADMIN_CHANGE_THRESHOLDS)),
):
    """Updates multimodal detection thresholds. Requires step-up TOTP verification."""
    user_store = UserStore.get_instance()
    user_obj = user_store.get_user_by_id(user.get("user_id", ""))
    
    if not verify_totp_code(user_obj.totp_secret or DEMO_TOTP_SECRET if user_obj else "", req.totp_code):
        raise HTTPException(status_code=400, detail="Invalid 2FA code. Threshold change rejected.")

    SYSTEM_THRESHOLDS["risk_threshold"] = req.risk_threshold
    SYSTEM_THRESHOLDS["face_weight"] = req.face_weight
    SYSTEM_THRESHOLDS["audio_weight"] = req.audio_weight
    SYSTEM_THRESHOLDS["temporal_weight"] = req.temporal_weight

    audit = SecurityAuditLogger.get_instance()
    audit.log_event(
        event_type="THRESHOLDS_UPDATED",
        payload={
            "updated_by": user.get("user_id"),
            "thresholds": SYSTEM_THRESHOLDS,
        },
    )
    return {"success": True, "thresholds": SYSTEM_THRESHOLDS}


# -----------------------------------------------------------------------------
# 8. Dev Mode Credentials Helper (For Frictionless Hackathon Evaluation)
# -----------------------------------------------------------------------------
@router.get("/auth/dev-credentials")
async def get_dev_credentials():
    """
    Returns active test credentials and live TOTP codes in DEV_MODE.
    Disabled in production.
    """
    if not DEV_MODE:
        raise HTTPException(status_code=404, detail="Not available in production mode.")

    active_totp = get_current_totp_code(DEMO_TOTP_SECRET)
    return {
        "dev_mode": True,
        "active_totp_code": active_totp,
        "demo_accounts": [
            {
                "role": "citizen",
                "label": "Citizen (Real-Time Protection)",
                "identifier": "citizen@demo.com",
                "otp_demo": "123456",
            },
            {
                "role": "forensic_officer",
                "label": "Forensic Officer (Court Analysis)",
                "email": "officer@court.demo",
                "password": "Demo@1234",
                "totp_secret": DEMO_TOTP_SECRET,
                "current_totp": active_totp,
            },
            {
                "role": "judge",
                "label": "Judge (Court Authority)",
                "email": "judge@court.demo",
                "password": "Demo@1234",
                "totp_secret": DEMO_TOTP_SECRET,
                "current_totp": active_totp,
            },
            {
                "role": "admin",
                "label": "Administrator (Full Access)",
                "email": "admin@securecall.demo",
                "password": "Demo@1234",
                "totp_secret": DEMO_TOTP_SECRET,
                "current_totp": active_totp,
            },
        ],
    }
