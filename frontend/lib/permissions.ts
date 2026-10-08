/**
 * SecureCall Role-Based Access Control (RBAC) Permission Matrix.
 * Canonical frontend mirror of backend/auth/permissions.py.
 * Reference this single file for all permission checks.
 */

export type Role = "citizen" | "forensic_officer" | "judge" | "admin";

export type Permission =
  // Live Call
  | "live_call.join"
  | "live_call.view_hud"
  | "live_call.inspect_evidence"
  | "live_call.register_reference_face"
  | "live_call.download_report"
  | "live_call.attach_to_case"
  // Bulk Verification
  | "bulk.create_case"
  | "bulk.upload_videos"
  | "bulk.run_detection"
  | "bulk.view_results"
  | "bulk.add_notes_generate_report"
  | "bulk.approve_report"
  // Audit & Evidence
  | "audit.verify_hash_chain"
  | "audit.view_custody_log"
  | "evidence.edit_or_delete"
  // Admin
  | "admin.manage_accounts"
  | "admin.assign_cases"
  | "admin.change_thresholds"
  | "admin.system_health";

export interface UserSession {
  user_id: string;
  name: string;
  role: Role;
  court_id?: string;
  assigned_cases?: string[];
  consent_given?: boolean;
}

export type PermissionRule =
  | "all"
  | "yes"
  | "no"
  | "own_calls"
  | "own_hearings"
  | "trusted_contacts"
  | "case_linked_persons"
  | "hearing_participants"
  | "assigned_cases"
  | "own_court"
  | "own_reports";

export const PERMISSION_MATRIX: Record<Permission, Record<Role, PermissionRule>> = {
  // Live Call
  "live_call.join": {
    citizen: "own_calls",
    forensic_officer: "own_calls",
    judge: "own_hearings",
    admin: "all",
  },
  "live_call.view_hud": {
    citizen: "own_calls",
    forensic_officer: "own_calls",
    judge: "own_hearings",
    admin: "all",
  },
  "live_call.inspect_evidence": {
    citizen: "own_calls",
    forensic_officer: "own_calls",
    judge: "own_hearings",
    admin: "all",
  },
  "live_call.register_reference_face": {
    citizen: "trusted_contacts",
    forensic_officer: "case_linked_persons",
    judge: "hearing_participants",
    admin: "all",
  },
  "live_call.download_report": {
    citizen: "own_calls",
    forensic_officer: "yes",
    judge: "yes",
    admin: "all",
  },
  "live_call.attach_to_case": {
    citizen: "no",
    forensic_officer: "yes",
    judge: "yes",
    admin: "yes",
  },

  // Bulk Verification
  "bulk.create_case": {
    citizen: "no",
    forensic_officer: "yes",
    judge: "no",
    admin: "yes",
  },
  "bulk.upload_videos": {
    citizen: "no",
    forensic_officer: "yes",
    judge: "no",
    admin: "yes",
  },
  "bulk.run_detection": {
    citizen: "no",
    forensic_officer: "yes",
    judge: "no",
    admin: "yes",
  },
  "bulk.view_results": {
    citizen: "no",
    forensic_officer: "assigned_cases",
    judge: "own_court",
    admin: "all",
  },
  "bulk.add_notes_generate_report": {
    citizen: "no",
    forensic_officer: "yes",
    judge: "no",
    admin: "yes",
  },
  "bulk.approve_report": {
    citizen: "no",
    forensic_officer: "no",
    judge: "yes",
    admin: "yes",
  },

  // Audit & Evidence
  "audit.verify_hash_chain": {
    citizen: "own_reports",
    forensic_officer: "yes",
    judge: "yes",
    admin: "yes",
  },
  "audit.view_custody_log": {
    citizen: "no",
    forensic_officer: "assigned_cases",
    judge: "own_court",
    admin: "all",
  },
  "evidence.edit_or_delete": {
    citizen: "no",
    forensic_officer: "no",
    judge: "no",
    admin: "yes",
  },

  // Admin
  "admin.manage_accounts": {
    citizen: "no",
    forensic_officer: "no",
    judge: "no",
    admin: "yes",
  },
  "admin.assign_cases": {
    citizen: "no",
    forensic_officer: "no",
    judge: "no",
    admin: "yes",
  },
  "admin.change_thresholds": {
    citizen: "no",
    forensic_officer: "no",
    judge: "no",
    admin: "yes",
  },
  "admin.system_health": {
    citizen: "no",
    forensic_officer: "no",
    judge: "no",
    admin: "yes",
  },
};

/**
 * Evaluates whether the given user has permission to perform an action.
 */
export function can(
  user: UserSession | null,
  permission: Permission,
  context?: Record<string, any>
): boolean {
  if (!user || !user.role) return false;

  const rule = PERMISSION_MATRIX[permission]?.[user.role] ?? "no";

  if (rule === "no") return false;
  if (rule === "all" || rule === "yes") return true;

  const ctx = context || {};

  if (rule === "own_calls" || rule === "own_hearings") {
    if (ctx.call_owner_id && user.user_id) {
      return ctx.call_owner_id === user.user_id;
    }
    return true;
  }

  if (rule === "assigned_cases") {
    if (!ctx.case_id) return true;
    return (user.assigned_cases || []).includes(ctx.case_id);
  }

  if (rule === "own_court") {
    if (!ctx.court_id) return true;
    return ctx.court_id === user.court_id;
  }

  if (rule === "own_reports") {
    if (ctx.report_user_id && user.user_id) {
      return ctx.report_user_id === user.user_id;
    }
    return true;
  }

  if (rule === "trusted_contacts" || rule === "case_linked_persons" || rule === "hearing_participants") {
    return true;
  }

  return false;
}
