"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  Scale,
  Video,
  CheckCircle2,
  ShieldCheck,
  LogOut,
  FolderOpen,
  ArrowRight,
  FileCheck,
  ShieldAlert,
  Loader2,
  Lock,
  RefreshCw,
  Hash,
  AlertTriangle,
} from "lucide-react";
import { getMe, logout, can, UserSession } from "@/lib/auth";
import { getApiBase } from "@/lib/config";
import OtpInput from "@/components/auth/OtpInput";

interface CourtCaseItem {
  case_id: string;
  title: string;
  description: string;
  court_id: string;
  assigned_officer_id: string;
  status: string;
  evidence_count: number;
}

export default function JudgeDashboardPage() {
  const router = useRouter();
  const [user, setUser] = useState<UserSession | null>(null);
  const [loading, setLoading] = useState(true);
  const [cases, setCases] = useState<CourtCaseItem[]>([]);
  const [loadingCases, setLoadingCases] = useState(false);

  // Approval TOTP Step-Up Modal State
  const [approvingCaseId, setApprovingCaseId] = useState<string | null>(null);
  const [totpCode, setTotpCode] = useState("");
  const [submittingApproval, setSubmittingApproval] = useState(false);
  const [approvalError, setApprovalError] = useState("");

  // Hash Chain Verification State
  const [verifyingChain, setVerifyingChain] = useState(false);
  const [chainResult, setChainResult] = useState<{
    valid: boolean;
    chain_length: number;
    broken_at_event_id?: number | null;
  } | null>(null);

  const loadCases = async () => {
    setLoadingCases(true);
    try {
      const res = await fetch(`${getApiBase()}/auth/cases`, {
        credentials: "include",
      });
      if (res.ok) {
        const data = await res.json();
        setCases(data);
      }
    } catch (e) {
      console.warn("Failed to load court cases:", e);
    } finally {
      setLoadingCases(false);
    }
  };

  useEffect(() => {
    getMe().then((u) => {
      if (!u) {
        router.push("/login/court");
      } else if (u.role !== "judge" && u.role !== "admin") {
        router.push("/dashboard/citizen");
      } else {
        setUser(u);
        loadCases();
      }
      setLoading(false);
    });
  }, [router]);

  const handleApproveReport = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!approvingCaseId || totpCode.length !== 6) {
      setApprovalError("Please provide a valid 6-digit TOTP authentication code.");
      return;
    }

    setSubmittingApproval(true);
    setApprovalError("");

    try {
      const res = await fetch(`${getApiBase()}/auth/cases/${approvingCaseId}/approve`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({
          totp_code: totpCode,
          action: "bulk.approve_report",
        }),
      });

      const data = await res.json();
      if (!res.ok) {
        setApprovalError(data.detail || "Approval authorization rejected.");
        return;
      }

      setApprovingCaseId(null);
      setTotpCode("");
      loadCases();
    } catch {
      setApprovalError("Network error while submitting judicial approval.");
    } finally {
      setSubmittingApproval(false);
    }
  };

  const handleVerifyChain = async () => {
    setVerifyingChain(true);
    try {
      const res = await fetch(`${getApiBase()}/auth/audit/verify`, {
        credentials: "include",
      });
      if (res.ok) {
        const data = await res.json();
        setChainResult(data);
      }
    } catch (e) {
      console.warn("Chain verification error:", e);
    } finally {
      setVerifyingChain(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-[calc(100vh-65px)] flex items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-amber-400" />
      </div>
    );
  }

  if (!user) return null;

  const canApprove = can(user, "bulk.approve_report");
  const canVerifyChain = can(user, "audit.verify_hash_chain");
  const canJoinHearing = can(user, "live_call.join");

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {/* Header Banner */}
      <div className="bg-gradient-to-r from-slate-900 via-slate-900 to-amber-950/40 border border-amber-500/30 rounded-2xl p-6 sm:p-8 backdrop-blur-xl shadow-xl flex flex-col md:flex-row md:items-center justify-between gap-6">
        <div>
          <div className="flex items-center gap-2 mb-2">
            <span className="text-xs font-mono font-semibold uppercase tracking-wider px-2.5 py-1 rounded-full bg-amber-500/10 text-amber-400 border border-amber-500/30">
              JUDICIAL BENCH & COURT AUTHORITY
            </span>
            <span className="text-xs font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700">
              JURISDICTION: {user.court_id || "court-central-01"}
            </span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-white">
            Honorable Judge {user.name || "Bench"}
          </h1>
          <p className="text-xs sm:text-sm text-slate-400 mt-1 max-w-xl">
            Judicial review of forensic deepfake evidence dossiers, pre-trial admissibility rulings, and cryptographic chain-of-custody verification.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={() => logout()}
            className="px-3.5 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white border border-slate-700 text-xs font-semibold flex items-center gap-2 transition-colors"
          >
            <LogOut className="w-3.5 h-3.5" />
            <span>Sign Out</span>
          </button>
        </div>
      </div>

      {/* Action Row */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Hearing Call Card */}
        <div className="bg-slate-900/80 border border-amber-500/30 rounded-2xl p-6 shadow-xl flex flex-col justify-between">
          <div>
            <div className="p-3 rounded-xl bg-amber-500/10 border border-amber-500/30 text-amber-400 w-fit mb-4">
              <Scale className="w-6 h-6" />
            </div>
            <h3 className="text-lg font-bold text-white mb-1">Start Remote Court Hearing</h3>
            <p className="text-xs text-slate-300 mb-6">
              Launch court hearing call with active deepfake inspection HUD to verify witness testimony and prevent impersonation.
            </p>
          </div>
          {canJoinHearing ? (
            <Link
              href="/call/judicial-hearing"
              className="w-full py-2.5 px-4 rounded-xl text-xs font-semibold text-white bg-gradient-to-r from-amber-600 to-amber-700 hover:from-amber-500 hover:to-amber-600 shadow-lg shadow-amber-950/40 flex items-center justify-center gap-2 transition-all"
            >
              <Video className="w-4 h-4" />
              <span>Convene Hearing Call</span>
            </Link>
          ) : (
            <button disabled className="w-full py-2.5 text-xs text-slate-600 bg-slate-800 rounded-xl cursor-not-allowed">
              Hearing Restricted
            </button>
          )}
        </div>

        {/* Cryptographic Hash Chain Audit Card */}
        <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 shadow-xl flex flex-col justify-between">
          <div>
            <div className="p-3 rounded-xl bg-purple-500/10 border border-purple-500/30 text-purple-400 w-fit mb-4">
              <Hash className="w-6 h-6" />
            </div>
            <h3 className="text-lg font-bold text-white mb-1">SHA-256 Custody Hash Chain</h3>
            <p className="text-xs text-slate-300 mb-4">
              Verify the unbroken cryptographic integrity of all forensic analysis logs, video hashes, and judicial approvals.
            </p>

            {chainResult && (
              <div
                className={`p-3 rounded-xl border text-xs mb-4 flex items-center gap-2 font-mono ${
                  chainResult.valid
                    ? "bg-emerald-500/10 border-emerald-500/30 text-emerald-300"
                    : "bg-rose-500/10 border-rose-500/30 text-rose-300"
                }`}
              >
                {chainResult.valid ? (
                  <>
                    <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
                    <span>Integrity Verified: {chainResult.chain_length} blocks forward-chained.</span>
                  </>
                ) : (
                  <>
                    <AlertTriangle className="w-4 h-4 text-rose-400 shrink-0" />
                    <span>Chain Tampered at block #{chainResult.broken_at_event_id}!</span>
                  </>
                )}
              </div>
            )}
          </div>

          {canVerifyChain ? (
            <button
              onClick={handleVerifyChain}
              disabled={verifyingChain}
              className="w-full py-2.5 px-4 rounded-xl text-xs font-semibold text-white bg-slate-800 hover:bg-slate-700 border border-slate-700 flex items-center justify-center gap-2 transition-colors disabled:opacity-50"
            >
              {verifyingChain ? (
                <Loader2 className="w-4 h-4 animate-spin text-purple-400" />
              ) : (
                <ShieldCheck className="w-4 h-4 text-purple-400" />
              )}
              <span>Verify Cryptographic Integrity</span>
            </button>
          ) : (
            <button disabled className="w-full py-2.5 text-xs text-slate-600 bg-slate-800 rounded-xl cursor-not-allowed">
              Audit Restricted
            </button>
          )}
        </div>
      </div>

      {/* Reports Awaiting Approval & Court Cases */}
      <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-bold text-white flex items-center gap-2">
              <FileCheck className="w-5 h-5 text-amber-400" /> Court Cases & Reports Awaiting Approval
            </h3>
            <p className="text-xs text-slate-400">
              Judicial review bench for jurisdiction: <span className="font-mono text-slate-300">{user.court_id}</span>
            </p>
          </div>
          <span className="text-xs font-mono text-amber-400 bg-amber-950/40 px-3 py-1 rounded-full border border-amber-800">
            {cases.length} Total Cases
          </span>
        </div>

        {loadingCases ? (
          <div className="py-8 text-center text-xs text-slate-400 flex items-center justify-center gap-2">
            <Loader2 className="w-4 h-4 animate-spin text-amber-400" />
            <span>Loading judicial cases...</span>
          </div>
        ) : cases.length === 0 ? (
          <div className="py-8 text-center text-xs text-slate-500">
            No pending court cases found in this jurisdiction.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-950/80 text-slate-400 border-b border-slate-800">
                <tr>
                  <th className="py-3 px-4">Case ID</th>
                  <th className="py-3 px-4">Title & Matter</th>
                  <th className="py-3 px-4">Assigned Officer</th>
                  <th className="py-3 px-4">Evidence</th>
                  <th className="py-3 px-4">Status</th>
                  <th className="py-3 px-4 text-right">Judicial Sign-off</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 font-mono">
                {cases.map((c) => (
                  <tr key={c.case_id} className="hover:bg-slate-950/40 transition-colors">
                    <td className="py-3 px-4 font-bold text-amber-400">{c.case_id}</td>
                    <td className="py-3 px-4 font-sans">
                      <div className="font-semibold text-white">{c.title}</div>
                      <div className="text-[11px] text-slate-400 line-clamp-1">{c.description}</div>
                    </td>
                    <td className="py-3 px-4 text-slate-400">{c.assigned_officer_id}</td>
                    <td className="py-3 px-4 text-white">{c.evidence_count} files</td>
                    <td className="py-3 px-4">
                      <span
                        className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                          c.status === "approved"
                            ? "bg-emerald-500/20 text-emerald-400 border border-emerald-500/30"
                            : "bg-amber-500/20 text-amber-400 border border-amber-500/30"
                        }`}
                      >
                        {c.status.toUpperCase()}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-right font-sans">
                      {c.status === "approved" ? (
                        <span className="text-emerald-400 font-semibold inline-flex items-center gap-1 text-[11px]">
                          <CheckCircle2 className="w-3.5 h-3.5" /> Approved & Signed
                        </span>
                      ) : canApprove ? (
                        <button
                          onClick={() => {
                            setApprovingCaseId(c.case_id);
                            setTotpCode("");
                            setApprovalError("");
                          }}
                          className="px-3 py-1.5 rounded-lg bg-amber-600 hover:bg-amber-500 text-white font-semibold text-xs inline-flex items-center gap-1.5 shadow-md shadow-amber-950/40"
                        >
                          <Lock className="w-3 h-3" />
                          <span>Approve Report</span>
                        </button>
                      ) : (
                        <span className="text-slate-600">Restricted</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* TOTP Step-Up Reauth Modal for Report Approval */}
      {approvingCaseId && (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-amber-500/40 rounded-2xl max-w-md w-full p-6 text-slate-200 shadow-2xl">
            <div className="flex items-center gap-2 mb-2 text-amber-400">
              <ShieldAlert className="w-5 h-5" />
              <h3 className="font-bold text-white text-base">Judicial Re-Authentication Required</h3>
            </div>
            <p className="text-xs text-slate-400 mb-4">
              Approving case report <span className="font-mono text-amber-400">{approvingCaseId}</span> enters an irrevocable judicial ruling into the SHA-256 chain of custody. Enter your 6-digit TOTP code to sign:
            </p>

            {approvalError && (
              <div className="p-3 rounded-lg border border-red-500/30 bg-red-950/40 text-red-300 text-xs mb-4">
                {approvalError}
              </div>
            )}

            <form onSubmit={handleApproveReport} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-2 text-center uppercase tracking-wider">
                  6-Digit Authenticator Code
                </label>
                <OtpInput
                  length={6}
                  value={totpCode}
                  onChange={setTotpCode}
                  onComplete={(code) => setTotpCode(code)}
                  disabled={submittingApproval}
                  ariaLabel="TOTP Code for Judicial Sign-Off"
                />
              </div>

              {/* Dev quick-fill */}
              <div className="p-2 rounded-lg bg-slate-950 border border-slate-800 text-[11px] text-slate-400 flex items-center justify-between font-mono">
                <span>Dev Master TOTP:</span>
                <button
                  type="button"
                  onClick={() => setTotpCode("123456")}
                  className="text-amber-400 hover:text-amber-300 underline font-semibold"
                >
                  Fill "123456"
                </button>
              </div>

              <div className="flex items-center justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => {
                    setApprovingCaseId(null);
                    setApprovalError("");
                  }}
                  className="px-3.5 py-2 rounded-xl bg-slate-800 text-slate-300 hover:text-white text-xs font-medium"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={totpCode.length !== 6 || submittingApproval}
                  className="px-4 py-2 rounded-xl bg-amber-600 hover:bg-amber-500 text-white text-xs font-semibold flex items-center gap-1.5 disabled:opacity-50"
                >
                  {submittingApproval ? (
                    <Loader2 className="w-3.5 h-3.5 animate-spin" />
                  ) : (
                    <CheckCircle2 className="w-3.5 h-3.5" />
                  )}
                  <span>Sign & Approve Case</span>
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
