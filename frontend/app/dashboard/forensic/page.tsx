"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  Scale,
  Video,
  Layers,
  PlusCircle,
  FileText,
  ShieldCheck,
  LogOut,
  FolderOpen,
  ArrowRight,
  Clock,
  CheckCircle2,
  AlertCircle,
  Loader2,
  Lock,
  Upload,
} from "lucide-react";
import { getMe, logout, can, UserSession } from "@/lib/auth";
import { getApiBase } from "@/lib/config";

interface CourtCaseItem {
  case_id: string;
  title: string;
  description: string;
  court_id: string;
  assigned_officer_id: string;
  status: string;
  evidence_count: number;
}

export default function ForensicDashboardPage() {
  const router = useRouter();
  const [user, setUser] = useState<UserSession | null>(null);
  const [loading, setLoading] = useState(true);
  const [cases, setCases] = useState<CourtCaseItem[]>([]);
  const [loadingCases, setLoadingCases] = useState(false);

  // New Case Modal State
  const [showNewCaseModal, setShowNewCaseModal] = useState(false);
  const [newTitle, setNewTitle] = useState("");
  const [newDesc, setNewDesc] = useState("");
  const [submittingCase, setSubmittingCase] = useState(false);
  const [caseError, setCaseError] = useState("");

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
      console.warn("Failed to load assigned cases:", e);
    } finally {
      setLoadingCases(false);
    }
  };

  useEffect(() => {
    getMe().then((u) => {
      if (!u) {
        router.push("/login/court");
      } else if (u.role !== "forensic_officer" && u.role !== "admin") {
        router.push("/dashboard/citizen");
      } else {
        setUser(u);
        loadCases();
      }
      setLoading(false);
    });
  }, [router]);

  const handleCreateCase = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newTitle.trim() || !newDesc.trim()) {
      setCaseError("Please provide both case title and investigation summary.");
      return;
    }

    setSubmittingCase(true);
    setCaseError("");

    try {
      const res = await fetch(`${getApiBase()}/auth/cases`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({
          title: newTitle.trim(),
          description: newDesc.trim(),
        }),
      });

      if (!res.ok) {
        const err = await res.json();
        setCaseError(err.detail || "Failed to create case.");
        return;
      }

      setShowNewCaseModal(false);
      setNewTitle("");
      setNewDesc("");
      loadCases();
    } catch {
      setCaseError("Network error creating case.");
    } finally {
      setSubmittingCase(false);
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

  const canCreateCase = can(user, "bulk.create_case");
  const canUploadVideos = can(user, "bulk.upload_videos");
  const canJoinCall = can(user, "live_call.join");
  const canApprove = can(user, "bulk.approve_report"); // false for officer

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {/* Header Banner */}
      <div className="bg-gradient-to-r from-slate-900 via-slate-900 to-amber-950/40 border border-amber-500/30 rounded-2xl p-6 sm:p-8 backdrop-blur-xl shadow-xl flex flex-col md:flex-row md:items-center justify-between gap-6">
        <div>
          <div className="flex items-center gap-2 mb-2">
            <span className="text-xs font-mono font-semibold uppercase tracking-wider px-2.5 py-1 rounded-full bg-amber-500/10 text-amber-400 border border-amber-500/30">
              FORENSIC EXAMINER CONSOLE
            </span>
            <span className="text-xs font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700">
              COURT: {user.court_id || "court-central-01"}
            </span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-white">
            Forensic Officer {user.name || "Examiner"}
          </h1>
          <p className="text-xs sm:text-sm text-slate-400 mt-1 max-w-xl">
            Court-appointed media forensic analysis. Multi-video batch deepfake extraction, Grad-CAM attention heatmaps, and evidentiary reports.
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
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Start Protected Call */}
        <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 shadow-xl flex flex-col justify-between">
          <div>
            <div className="p-3 rounded-xl bg-cyan-500/10 border border-cyan-500/30 text-cyan-400 w-fit mb-4">
              <Video className="w-6 h-6" />
            </div>
            <h3 className="text-lg font-bold text-white mb-1">Live Call Examination</h3>
            <p className="text-xs text-slate-300 mb-6">
              Launch real-time forensics HUD for witness depositions, remote testimony, or suspect video feeds.
            </p>
          </div>
          {canJoinCall ? (
            <Link
              href="/call/forensic-session"
              className="w-full py-2.5 px-4 rounded-xl text-xs font-semibold text-white bg-slate-800 hover:bg-slate-700 border border-slate-700 flex items-center justify-center gap-2 transition-colors"
            >
              <Video className="w-4 h-4 text-cyan-400" />
              <span>Launch Live Call HUD</span>
            </Link>
          ) : (
            <button disabled className="w-full py-2.5 text-xs text-slate-600 bg-slate-800 rounded-xl cursor-not-allowed">
              Restricted
            </button>
          )}
        </div>

        {/* Bulk Verification Hub */}
        <div className="bg-slate-900/80 border border-amber-500/30 rounded-2xl p-6 shadow-xl flex flex-col justify-between">
          <div>
            <div className="p-3 rounded-xl bg-amber-500/10 border border-amber-500/30 text-amber-400 w-fit mb-4">
              <Layers className="w-6 h-6" />
            </div>
            <h3 className="text-lg font-bold text-white mb-1">Bulk Video Verification</h3>
            <p className="text-xs text-slate-300 mb-6">
              Upload batches or complete folders of video evidence for parallel frame-by-frame deepfake classification.
            </p>
          </div>
          {canUploadVideos ? (
            <Link
              href="/bulk"
              className="w-full py-2.5 px-4 rounded-xl text-xs font-semibold text-white bg-gradient-to-r from-amber-600 to-amber-700 hover:from-amber-500 hover:to-amber-600 shadow-lg shadow-amber-950/40 flex items-center justify-center gap-2 transition-all"
            >
              <Upload className="w-4 h-4" />
              <span>Open Bulk Verification Lab</span>
            </Link>
          ) : (
            <button disabled className="w-full py-2.5 text-xs text-slate-600 bg-slate-800 rounded-xl cursor-not-allowed">
              Upload Restricted
            </button>
          )}
        </div>

        {/* Create Case Dossier */}
        <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 shadow-xl flex flex-col justify-between">
          <div>
            <div className="p-3 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 w-fit mb-4">
              <FolderOpen className="w-6 h-6" />
            </div>
            <h3 className="text-lg font-bold text-white mb-1">Evidentiary Case Dossiers</h3>
            <p className="text-xs text-slate-300 mb-6">
              Open a new official forensic case tied to your court jurisdiction and generate formal court reports.
            </p>
          </div>
          {canCreateCase ? (
            <button
              onClick={() => setShowNewCaseModal(true)}
              className="w-full py-2.5 px-4 rounded-xl text-xs font-semibold text-white bg-emerald-700 hover:bg-emerald-600 flex items-center justify-center gap-2 transition-colors shadow-lg shadow-emerald-950/40"
            >
              <PlusCircle className="w-4 h-4" />
              <span>Register New Case</span>
            </button>
          ) : (
            <button disabled className="w-full py-2.5 text-xs text-slate-600 bg-slate-800 rounded-xl cursor-not-allowed">
              Creation Restricted
            </button>
          )}
        </div>
      </div>

      {/* Assigned Cases List */}
      <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-bold text-white flex items-center gap-2">
              <FolderOpen className="w-5 h-5 text-amber-400" /> My Assigned Court Cases
            </h3>
            <p className="text-xs text-slate-400">
              Cases assigned to officer ID: <span className="font-mono text-slate-300">{user.user_id}</span>
            </p>
          </div>
          <span className="text-xs font-mono text-amber-400 bg-amber-950/40 px-3 py-1 rounded-full border border-amber-800">
            {cases.length} Active Dossiers
          </span>
        </div>

        {loadingCases ? (
          <div className="py-8 text-center text-xs text-slate-400 flex items-center justify-center gap-2">
            <Loader2 className="w-4 h-4 animate-spin text-amber-400" />
            <span>Retrieving court cases...</span>
          </div>
        ) : cases.length === 0 ? (
          <div className="py-8 text-center text-xs text-slate-500">
            No court cases currently assigned. Click "Register New Case" above to initiate an investigation.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-950/80 text-slate-400 border-b border-slate-800">
                <tr>
                  <th className="py-3 px-4">Case ID</th>
                  <th className="py-3 px-4">Case Title & Summary</th>
                  <th className="py-3 px-4">Court Jurisdiction</th>
                  <th className="py-3 px-4">Evidence Count</th>
                  <th className="py-3 px-4">Case Status</th>
                  <th className="py-3 px-4 text-right">Approval Status</th>
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
                    <td className="py-3 px-4 text-slate-400">{c.court_id}</td>
                    <td className="py-3 px-4 text-white">{c.evidence_count} items</td>
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
                        <span className="text-emerald-400 font-semibold flex items-center justify-end gap-1 text-[11px]">
                          <CheckCircle2 className="w-3.5 h-3.5" /> Approved by Judge
                        </span>
                      ) : (
                        <span className="text-slate-400 text-[11px] flex items-center justify-end gap-1" title="Forensic officers cannot approve reports">
                          <Lock className="w-3 h-3 text-amber-500" /> Pending Judge Sign-Off
                        </span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* New Case Modal */}
      {showNewCaseModal && (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-amber-500/30 rounded-2xl max-w-md w-full p-6 text-slate-200 shadow-2xl">
            <h3 className="text-lg font-bold text-white mb-2">Register Court Case Dossier</h3>
            <p className="text-xs text-slate-400 mb-4">
              Create an evidentiary investigation dossier under court {user.court_id}.
            </p>

            {caseError && (
              <div className="p-3 rounded-lg border border-red-500/30 bg-red-950/40 text-red-300 text-xs mb-4">
                {caseError}
              </div>
            )}

            <form onSubmit={handleCreateCase} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1 uppercase">Case Title</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. State v. Marcus Vance — Wire Fraud Media"
                  value={newTitle}
                  onChange={(e) => setNewTitle(e.target.value)}
                  className="w-full px-3.5 py-2 rounded-xl bg-slate-950 border border-slate-700 text-white text-xs focus:outline-none focus:border-amber-400"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1 uppercase">Investigation Summary</label>
                <textarea
                  rows={3}
                  required
                  placeholder="Suspect video voice clone manipulation analysis requested for pre-trial admissibility hearing..."
                  value={newDesc}
                  onChange={(e) => setNewDesc(e.target.value)}
                  className="w-full px-3.5 py-2 rounded-xl bg-slate-950 border border-slate-700 text-white text-xs focus:outline-none focus:border-amber-400 resize-none"
                />
              </div>

              <div className="flex items-center justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setShowNewCaseModal(false)}
                  className="px-3.5 py-2 rounded-xl bg-slate-800 text-slate-300 hover:text-white text-xs font-medium"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submittingCase}
                  className="px-4 py-2 rounded-xl bg-amber-600 hover:bg-amber-500 text-white text-xs font-semibold flex items-center gap-1.5 disabled:opacity-50"
                >
                  {submittingCase ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <PlusCircle className="w-3.5 h-3.5" />}
                  <span>Create Dossier</span>
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
