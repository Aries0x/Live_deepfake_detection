"""
SecureCall Role-Based Access Control (RBAC) Permission Matrix.
Canonical single source of truth for all role permissions and scope constraints.
Roles:
  - citizen: public user, real-time protection only
  - forensic_officer: court-appointed examiner, real-time + bulk analysis
  - judge: court authority, real-time + reviews/approves bulk reports
  - admin: full access to everything
"""
from enum import Enum
from typing import Dict, Any, Optional, List


class Role(str, Enum):
    CITIZEN = "citizen"
    FORENSIC_OFFICER = "forensic_officer"
    JUDGE = "judge"
    ADMIN = "admin"


class Permission(str, Enum):
    # Live Call Permissions
    LIVE_CALL_JOIN = "live_call.join"
    LIVE_CALL_VIEW_HUD = "live_call.view_hud"
    LIVE_CALL_INSPECT_EVIDENCE = "live_call.inspect_evidence"
    LIVE_CALL_REGISTER_REFERENCE_FACE = "live_call.register_reference_face"
    LIVE_CALL_DOWNLOAD_REPORT = "live_call.download_report"
    LIVE_CALL_ATTACH_TO_CASE = "live_call.attach_to_case"

    # Bulk Verification & Court Case Permissions
    BULK_CREATE_CASE = "bulk.create_case"
    BULK_UPLOAD_VIDEOS = "bulk.upload_videos"
    BULK_RUN_DETECTION = "bulk.run_detection"
    BULK_VIEW_RESULTS = "bulk.view_results"
    BULK_ADD_NOTES_GENERATE_REPORT = "bulk.add_notes_generate_report"
    BULK_APPROVE_REPORT = "bulk.approve_report"

    # Tamper-Evident Audit & Evidence Custody
    AUDIT_VERIFY_HASH_CHAIN = "audit.verify_hash_chain"
    AUDIT_VIEW_CUSTODY_LOG = "audit.view_custody_log"
    EVIDENCE_EDIT_OR_DELETE = "evidence.edit_or_delete"

    # Administration
    ADMIN_MANAGE_ACCOUNTS = "admin.manage_accounts"
    ADMIN_ASSIGN_CASES = "admin.assign_cases"
    ADMIN_CHANGE_THRESHOLDS = "admin.change_thresholds"
    ADMIN_SYSTEM_HEALTH = "admin.system_health"


# Canonical Matrix: (Permission, Role) -> Scope / Rule
# Rules:
#   "all" / "yes": completely allowed
#   "no": forbidden
#   "own_calls": allowed only for calls started or joined by the user
#   "trusted_contacts": allowed for own trusted contacts with consent
#   "case_linked_persons": allowed for individuals associated with assigned court cases
#   "hearing_participants": allowed for participants in own court hearings
#   "assigned_cases": allowed for cases assigned to the officer
#   "own_court": allowed for cases under the judge's court jurisdiction
#   "own_reports": allowed for reports originating from user's sessions
PERMISSION_MATRIX: Dict[Permission, Dict[Role, str]] = {
    # Live Call
    Permission.LIVE_CALL_JOIN: {
        Role.CITIZEN: "own_calls",
        Role.FORENSIC_OFFICER: "own_calls",
        Role.JUDGE: "own_hearings",
        Role.ADMIN: "all",
    },
    Permission.LIVE_CALL_VIEW_HUD: {
        Role.CITIZEN: "own_calls",
        Role.FORENSIC_OFFICER: "own_calls",
        Role.JUDGE: "own_hearings",
        Role.ADMIN: "all",
    },
    Permission.LIVE_CALL_INSPECT_EVIDENCE: {
        Role.CITIZEN: "own_calls",
        Role.FORENSIC_OFFICER: "own_calls",
        Role.JUDGE: "own_hearings",
        Role.ADMIN: "all",
    },
    Permission.LIVE_CALL_REGISTER_REFERENCE_FACE: {
        Role.CITIZEN: "trusted_contacts",
        Role.FORENSIC_OFFICER: "case_linked_persons",
        Role.JUDGE: "hearing_participants",
        Role.ADMIN: "all",
    },
    Permission.LIVE_CALL_DOWNLOAD_REPORT: {
        Role.CITIZEN: "own_calls",
        Role.FORENSIC_OFFICER: "yes",
        Role.JUDGE: "yes",
        Role.ADMIN: "all",
    },
    Permission.LIVE_CALL_ATTACH_TO_CASE: {
        Role.CITIZEN: "no",
        Role.FORENSIC_OFFICER: "yes",
        Role.JUDGE: "yes",
        Role.ADMIN: "yes",
    },

    # Bulk Verification
    Permission.BULK_CREATE_CASE: {
        Role.CITIZEN: "no",
        Role.FORENSIC_OFFICER: "yes",
        Role.JUDGE: "no",
        Role.ADMIN: "yes",
    },
    Permission.BULK_UPLOAD_VIDEOS: {
        Role.CITIZEN: "no",
        Role.FORENSIC_OFFICER: "yes",
        Role.JUDGE: "no",
        Role.ADMIN: "yes",
    },
    Permission.BULK_RUN_DETECTION: {
        Role.CITIZEN: "no",
        Role.FORENSIC_OFFICER: "yes",
        Role.JUDGE: "no",
        Role.ADMIN: "yes",
    },
    Permission.BULK_VIEW_RESULTS: {
        Role.CITIZEN: "no",
        Role.FORENSIC_OFFICER: "assigned_cases",
        Role.JUDGE: "own_court",
        Role.ADMIN: "all",
    },
    Permission.BULK_ADD_NOTES_GENERATE_REPORT: {
        Role.CITIZEN: "no",
        Role.FORENSIC_OFFICER: "yes",
        Role.JUDGE: "no",
        Role.ADMIN: "yes",
    },
    Permission.BULK_APPROVE_REPORT: {
        Role.CITIZEN: "no",
        Role.FORENSIC_OFFICER: "no",
        Role.JUDGE: "yes",
        Role.ADMIN: "yes",
    },

    # Audit & Evidence
    Permission.AUDIT_VERIFY_HASH_CHAIN: {
        Role.CITIZEN: "own_reports",
        Role.FORENSIC_OFFICER: "yes",
        Role.JUDGE: "yes",
        Role.ADMIN: "yes",
    },
    Permission.AUDIT_VIEW_CUSTODY_LOG: {
        Role.CITIZEN: "no",
        Role.FORENSIC_OFFICER: "assigned_cases",
        Role.JUDGE: "own_court",
        Role.ADMIN: "all",
    },
    Permission.EVIDENCE_EDIT_OR_DELETE: {
        Role.CITIZEN: "no",
        Role.FORENSIC_OFFICER: "no",
        Role.JUDGE: "no",
        Role.ADMIN: "yes",  # Must be logged to hash chain
    },

    # Admin
    Permission.ADMIN_MANAGE_ACCOUNTS: {
        Role.CITIZEN: "no",
        Role.FORENSIC_OFFICER: "no",
        Role.JUDGE: "no",
        Role.ADMIN: "yes",
    },
    Permission.ADMIN_ASSIGN_CASES: {
        Role.CITIZEN: "no",
        Role.FORENSIC_OFFICER: "no",
        Role.JUDGE: "no",
        Role.ADMIN: "yes",
    },
    Permission.ADMIN_CHANGE_THRESHOLDS: {
        Role.CITIZEN: "no",
        Role.FORENSIC_OFFICER: "no",
        Role.JUDGE: "no",
        Role.ADMIN: "yes",
    },
    Permission.ADMIN_SYSTEM_HEALTH: {
        Role.CITIZEN: "no",
        Role.FORENSIC_OFFICER: "no",
        Role.JUDGE: "no",
        Role.ADMIN: "yes",
    },
}


def can_perform(user: Dict[str, Any], permission: Permission | str, context: Optional[Dict[str, Any]] = None) -> bool:
    """
    Evaluates whether the given user has permission to perform an action,
    taking into account their role and runtime context (e.g. case ID, court ID, call ID).
    """
    if not user:
        return False

    role_str = user.get("role", "")
    try:
        role = Role(role_str)
    except ValueError:
        return False

    try:
        perm = Permission(permission) if isinstance(permission, str) else permission
    except ValueError:
        return False

    perm_rules = PERMISSION_MATRIX.get(perm, {})
    rule = perm_rules.get(role, "no")

    if rule == "no":
        return False

    if rule in ("all", "yes"):
        return True

    ctx = context or {}

    # Contextual scope evaluations
    if rule in ("own_calls", "own_hearings"):
        call_id = ctx.get("call_id")
        owner_id = ctx.get("call_owner_id")
        user_id = user.get("user_id")
        if owner_id and user_id:
            return owner_id == user_id
        # If user is in the participants list
        participants = ctx.get("participants", [])
        if user_id in participants:
            return True
        return True  # If no specific call owner is passed, allow creating/joining own call

    if rule == "assigned_cases":
        case_id = ctx.get("case_id")
        if not case_id:
            return True  # Listing assigned cases
        assigned_cases = user.get("assigned_cases") or []
        return case_id in assigned_cases

    if rule == "own_court":
        case_court_id = ctx.get("court_id")
        user_court_id = user.get("court_id")
        if not case_court_id:
            return True  # Listing court cases
        return case_court_id == user_court_id

    if rule == "own_reports":
        report_user_id = ctx.get("report_user_id")
        user_id = user.get("user_id")
        if report_user_id and user_id:
            return report_user_id == user_id
        return True

    if rule in ("trusted_contacts", "case_linked_persons", "hearing_participants"):
        return True

    return False
