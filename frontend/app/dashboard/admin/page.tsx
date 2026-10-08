"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  ShieldAlert,
  Users,
  FolderOpen,
  Video,
  Sliders,
  Activity,
  Hash,
  LogOut,
  CheckCircle2,
  AlertTriangle,
  Loader2,
  Lock,
  RefreshCw,
  Save,
  Check,
} from "lucide-react";
import { getMe, logout, can, UserSession } from "@/lib/auth";
import { getApiBase } from "@/lib/config";
import OtpInput from "@/components/auth/OtpInput";

type AdminTab = "users" | "cases" | "calls" | "thresholds" | "health" | "audit";

export default function AdminDashboardPage() {
  const router = useRouter();
  const [user, setUser] = useState<UserSession | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<AdminTab>("users");

  // Tab Data States
  const [usersList, setUsersList] = useState<any[]>([]);
  const [casesList, setCasesList] = useState<any[]>([]);
  const [healthData, setHealthData] = useState<any>(null);
  const [auditChain, setAuditChain] = useState<any[]>([]);
  const [chainVerifyResult, setChainVerifyResult] = useState<any>(null);

  // Thresholds State
  const [thresholds, setThresholds] = useState({
    risk_threshold: 0.65,
    face_weight: 0.5,
    audio_weight: 0.3,
    temporal_weight: 0.2,
  });
  const [showTotpModal, setShowTotpModal] = useState(false);
  const [totpCode, setTotpCode] = useState("");
  const [savingThresholds, setSavingThresholds] = useState(false);
  const [thresholdMsg, setThresholdMsg] = useState<{ type: "success" | "error"; text: string } | null>(null);

  // Load Admin Data
  const loadUsers = async () => {
    try {
      const res = await fetch(`${getApiBase()}/auth/admin/users`, { credentials: "include" });
      if (res.ok) setUsersList(await res.json());
    } catch (e) {
      console.warn("Failed to load users:", e);
    }
  };

  const loadCases = async () => {
    try {
      const res = await fetch(`${getApiBase()}/auth/cases`, { credentials: "include" });
      if (res.ok) setCasesList(await res.json());
    } catch (e) {
      console.warn("Failed to load cases:", e);
    }
  };

  const loadThresholds = async () => {
    try {
      const res = await fetch(`${getApiBase()}/auth/admin/thresholds`, { credentials: "include" });
      if (res.ok) setThresholds(await res.json());
    } catch (e) {
      console.warn("Failed to load thresholds:", e);
    }
  };

  const loadHealth = async () => {
    try {
      const res = await fetch(`${getApiBase()}/api/v1/health`);
      if (res.ok) setHealthData(await res.json());
    } catch (e) {
      console.warn("Failed to load health:", e);
    }
  };

  const loadAuditChain = async () => {
    try {
      const res = await fetch(`${getApiBase()}/auth/audit/chain`, { credentials: "include" });
      if (res.ok) {
        const data = await res.json();
        setAuditChain(data.events || []);
      }
    } catch (e) {
      console.warn("Failed to load audit chain:", e);
    }
  };

  const verifyAuditChain = async () => {
    try {
      const res = await fetch(`${getApiBase()}/auth/audit/verify`, { credentials: "include" });
      if (res.ok) {
        setChainVerifyResult(await res.json());
      }
    } catch (e) {
      console.warn("Chain verify error:", e);
    }
  };

  useEffect(() => {
    getMe().then((u) => {
      if (!u) {
        router.push("/login/admin");
      } else if (u.role !== "admin") {
        router.push("/dashboard/citizen");
      } else {
        setUser(u);
        loadUsers();
        loadCases();
        loadThresholds();
        loadHealth();
        loadAuditChain();
      }
      setLoading(false);
    });
  }, [router]);

  const handleSaveThresholds = async (e: React.FormEvent) => {
    e.preventDefault();
    if (totpCode.length !== 6) {
      setThresholdMsg({ type: "error", text: "Please enter the 6-digit TOTP code." });
      return;
    }

    setSavingThresholds(true);
    setThresholdMsg(null);

    try {
      const res = await fetch(`${getApiBase()}/auth/admin/thresholds`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({
          ...thresholds,
          totp_code: totpCode,
        }),
      });

      const data = await res.json();
      if (!res.ok) {
        setThresholdMsg({ type: "error", text: data.detail || "Failed to update thresholds." });
        return;
      }

      setThresholdMsg({ type: "success", text: "Thresholds successfully updated and recorded in the audit chain!" });
      setShowTotpModal(false);
      setTotpCode("");
      loadAuditChain();
    } catch {
      setThresholdMsg({ type: "error", text: "Network error saving thresholds." });
    } finally {
      setSavingThresholds(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-[calc(100vh-65px)] flex items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-rose-500" />
      </div>
    );
  }

  if (!user) return null;

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {/* Header Banner */}
      <div className="bg-gradient-to-r from-slate-900 via-slate-900 to-rose-950/40 border border-rose-500/30 rounded-2xl p-6 sm:p-8 backdrop-blur-xl shadow-xl flex flex-col md:flex-row md:items-center justify-between gap-6">
        <div>
          <div className="flex items-center gap-2 mb-2">
            <span className="text-xs font-mono font-semibold uppercase tracking-wider px-2.5 py-1 rounded-full bg-rose-500/10 text-rose-400 border border-rose-500/30">
              SYSTEM SUPERUSER CONSOLE
            </span>
            <span className="text-xs font-mono px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
              ROOT AUTHORIZED
            </span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-white">
            SecureCall Root Administrator
          </h1>
          <p className="text-xs sm:text-sm text-slate-400 mt-1 max-w-xl">
            Full platform governance: account provisioning, forensic threshold tuning, hardware telemetry, and SHA-256 hash chain auditing.
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

      {/* Tabs Navigation */}
      <div className="flex flex-wrap items-center gap-2 border-b border-slate-800 pb-4">
        {[
          { id: "users", label: "Users & Accounts", icon: Users },
          { id: "cases", label: "Cases & Dossiers", icon: FolderOpen },
          { id: "calls", label: "All Calls", icon: Video },
          { id: "thresholds", label: "Detection Thresholds", icon: Sliders },
          { id: "health", label: "System Health", icon: Activity },
          { id: "audit", label: "Hash Chain Audit Log", icon: Hash },
        ].map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as AdminTab)}
              className={`flex items-center gap-2 px-4 py-2.5 rounded-xl text-xs font-semibold transition-all ${
                isActive
                  ? "bg-rose-600 text-white shadow-lg shadow-rose-950/40"
                  : "bg-slate-900/60 text-slate-400 hover:text-white hover:bg-slate-800 border border-slate-800"
              }`}
            >
              <Icon className="w-4 h-4" />
              <span>{tab.label}</span>
            </button>
          );
        })}
      </div>

      {/* Tab 1: Users */}
      {activeTab === "users" && (
        <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-base font-bold text-white flex items-center gap-2">
              <Users className="w-4 h-4 text-rose-400" /> Platform Accounts & RBAC Assignment
            </h3>
            <span className="text-xs font-mono text-slate-400">{usersList.length} Accounts Registered</span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs font-mono">
              <thead className="bg-slate-950 text-slate-400 border-b border-slate-800 font-sans">
                <tr>
                  <th className="py-2.5 px-3">User ID</th>
                  <th className="py-2.5 px-3">Display Name</th>
                  <th className="py-2.5 px-3">Identifier / Email</th>
                  <th className="py-2.5 px-3">Role</th>
                  <th className="py-2.5 px-3">Court / Scope</th>
                  <th className="py-2.5 px-3">Security Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {usersList.map((u) => (
                  <tr key={u.id} className="hover:bg-slate-950/40">
                    <td className="py-2.5 px-3 text-slate-400">{u.id}</td>
                    <td className="py-2.5 px-3 text-white font-sans font-medium">{u.name}</td>
                    <td className="py-2.5 px-3 text-slate-300">{u.identifier}</td>
                    <td className="py-2.5 px-3 font-sans">
                      <span
                        className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                          u.role === "admin"
                            ? "bg-rose-500/20 text-rose-400 border border-rose-500/30"
                            : u.role === "judge" || u.role === "forensic_officer"
                            ? "bg-amber-500/20 text-amber-400 border border-amber-500/30"
                            : "bg-cyan-500/20 text-cyan-400 border border-cyan-500/30"
                        }`}
                      >
                        {u.role.toUpperCase()}
                      </span>
                    </td>
                    <td className="py-2.5 px-3 text-slate-400 font-sans">{u.court_id || "Public / All"}</td>
                    <td className="py-2.5 px-3 font-sans">
                      {u.is_locked ? (
                        <span className="text-rose-400 text-[11px] font-semibold flex items-center gap-1">
                          <Lock className="w-3 h-3" /> Locked
                        </span>
                      ) : (
                        <span className="text-emerald-400 text-[11px] font-semibold flex items-center gap-1">
                          <CheckCircle2 className="w-3 h-3" /> Active
                        </span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Tab 2: Cases */}
      {activeTab === "cases" && (
        <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-base font-bold text-white flex items-center gap-2">
              <FolderOpen className="w-4 h-4 text-amber-400" /> Court Evidence Cases (System-Wide)
            </h3>
            <span className="text-xs font-mono text-slate-400">{casesList.length} Total Dossiers</span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs font-mono">
              <thead className="bg-slate-950 text-slate-400 border-b border-slate-800 font-sans">
                <tr>
                  <th className="py-2.5 px-3">Case ID</th>
                  <th className="py-2.5 px-3">Title</th>
                  <th className="py-2.5 px-3">Court</th>
                  <th className="py-2.5 px-3">Assigned Officer</th>
                  <th className="py-2.5 px-3">Evidence</th>
                  <th className="py-2.5 px-3">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {casesList.map((c) => (
                  <tr key={c.case_id} className="hover:bg-slate-950/40">
                    <td className="py-2.5 px-3 text-amber-400 font-bold">{c.case_id}</td>
                    <td className="py-2.5 px-3 text-white font-sans">{c.title}</td>
                    <td className="py-2.5 px-3 text-slate-400">{c.court_id}</td>
                    <td className="py-2.5 px-3 text-slate-400">{c.assigned_officer_id}</td>
                    <td className="py-2.5 px-3 text-white">{c.evidence_count}</td>
                    <td className="py-2.5 px-3 font-sans">
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
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Tab 3: All Calls */}
      {activeTab === "calls" && (
        <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-base font-bold text-white flex items-center gap-2">
              <Video className="w-4 h-4 text-cyan-400" /> Active & Archived Live WebRTC Calls
            </h3>
            <Link
              href="/call/admin-monitor"
              className="px-3 py-1.5 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white text-xs font-semibold flex items-center gap-1.5"
            >
              <Video className="w-3.5 h-3.5" /> Connect to Monitor Room
            </Link>
          </div>
          <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 text-xs text-slate-400">
            Real-time WebRTC media inspection hub. Admin has global join and HUD monitoring rights across all active rooms.
          </div>
        </div>
      )}

      {/* Tab 4: Thresholds */}
      {activeTab === "thresholds" && (
        <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-6 max-w-2xl">
          <div>
            <h3 className="text-base font-bold text-white flex items-center gap-2">
              <Sliders className="w-4 h-4 text-rose-400" /> Multimodal Detection Thresholds
            </h3>
            <p className="text-xs text-slate-400 mt-1">
              Adjust sensitivity for facial manipulation, audio anti-spoofing, and temporal consistency. Modifying these parameters requires mandatory TOTP confirmation and is permanently logged to the SHA-256 hash chain.
            </p>
          </div>

          {thresholdMsg && (
            <div
              className={`p-3 rounded-xl border text-xs flex items-center gap-2 ${
                thresholdMsg.type === "success"
                  ? "bg-emerald-500/10 border-emerald-500/30 text-emerald-300"
                  : "bg-rose-500/10 border-rose-500/30 text-rose-300"
              }`}
            >
              {thresholdMsg.type === "success" ? <Check className="w-4 h-4" /> : <AlertTriangle className="w-4 h-4" />}
              <span>{thresholdMsg.text}</span>
            </div>
          )}

          <div className="space-y-4">
            <div>
              <div className="flex justify-between text-xs font-semibold text-slate-300 mb-1">
                <span>Deepfake Risk Threshold (Overall)</span>
                <span className="font-mono text-rose-400">{(thresholds.risk_threshold * 100).toFixed(0)}%</span>
              </div>
              <input
                type="range"
                min="0.1"
                max="0.95"
                step="0.05"
                value={thresholds.risk_threshold}
                onChange={(e) => setThresholds({ ...thresholds, risk_threshold: parseFloat(e.target.value) })}
                className="w-full accent-rose-500"
              />
            </div>

            <div>
              <div className="flex justify-between text-xs font-semibold text-slate-300 mb-1">
                <span>Face Manipulation Weight (Spatial / Grad-CAM)</span>
                <span className="font-mono text-cyan-400">{(thresholds.face_weight * 100).toFixed(0)}%</span>
              </div>
              <input
                type="range"
                min="0.1"
                max="0.9"
                step="0.05"
                value={thresholds.face_weight}
                onChange={(e) => setThresholds({ ...thresholds, face_weight: parseFloat(e.target.value) })}
                className="w-full accent-cyan-500"
              />
            </div>

            <div>
              <div className="flex justify-between text-xs font-semibold text-slate-300 mb-1">
                <span>Audio Anti-Spoofing Weight (Spectral / Clone)</span>
                <span className="font-mono text-amber-400">{(thresholds.audio_weight * 100).toFixed(0)}%</span>
              </div>
              <input
                type="range"
                min="0.1"
                max="0.9"
                step="0.05"
                value={thresholds.audio_weight}
                onChange={(e) => setThresholds({ ...thresholds, audio_weight: parseFloat(e.target.value) })}
                className="w-full accent-amber-500"
              />
            </div>

            <div>
              <div className="flex justify-between text-xs font-semibold text-slate-300 mb-1">
                <span>Temporal Consistency Weight (Blink / Flow)</span>
                <span className="font-mono text-purple-400">{(thresholds.temporal_weight * 100).toFixed(0)}%</span>
              </div>
              <input
                type="range"
                min="0.1"
                max="0.9"
                step="0.05"
                value={thresholds.temporal_weight}
                onChange={(e) => setThresholds({ ...thresholds, temporal_weight: parseFloat(e.target.value) })}
                className="w-full accent-purple-500"
              />
            </div>
          </div>

          <button
            onClick={() => setShowTotpModal(true)}
            className="px-5 py-2.5 rounded-xl bg-rose-600 hover:bg-rose-500 text-white font-semibold text-xs flex items-center gap-2 shadow-lg shadow-rose-950/40"
          >
            <Lock className="w-3.5 h-3.5" />
            <span>Apply Threshold Updates (Requires 2FA)</span>
          </button>
        </div>
      )}

      {/* Tab 5: System Health */}
      {activeTab === "health" && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-2">
            <span className="text-xs font-mono text-slate-400 uppercase">GPU Acceleration</span>
            <p className="text-xl font-bold text-white">{healthData?.gpu?.name || "CUDA Ready"}</p>
            <span className="text-[11px] text-emerald-400 font-semibold block">Hardware Initialized</span>
          </div>

          <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-2">
            <span className="text-xs font-mono text-slate-400 uppercase">Inference Backend</span>
            <p className="text-xl font-bold text-emerald-400">{healthData?.backend === "ok" ? "ONLINE" : "READY"}</p>
            <span className="text-[11px] text-slate-400 block font-mono">FastAPI Port 8000</span>
          </div>

          <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-2">
            <span className="text-xs font-mono text-slate-400 uppercase">Audit Chain Status</span>
            <p className="text-xl font-bold text-purple-400">{auditChain.length} Blocks</p>
            <span className="text-[11px] text-emerald-400 font-semibold block">Forward Chaining Active</span>
          </div>
        </div>
      )}

      {/* Tab 6: Audit Log */}
      {activeTab === "audit" && (
        <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div>
              <h3 className="text-base font-bold text-white flex items-center gap-2">
                <Hash className="w-4 h-4 text-purple-400" /> Tamper-Evident SHA-256 Audit Forward Chain
              </h3>
              <p className="text-xs text-slate-400">
                Every login, logout, failed attempt, 2FA verify, and approval is immutably anchored.
              </p>
            </div>
            <button
              onClick={verifyAuditChain}
              className="px-4 py-2 rounded-xl bg-purple-700 hover:bg-purple-600 text-white text-xs font-semibold flex items-center gap-1.5 shadow-lg shadow-purple-950/40"
            >
              <CheckCircle2 className="w-4 h-4" />
              <span>Verify Chain Integrity</span>
            </button>
          </div>

          {chainVerifyResult && (
            <div
              className={`p-3.5 rounded-xl border text-xs font-mono flex items-center gap-2 ${
                chainVerifyResult.valid
                  ? "bg-emerald-500/10 border-emerald-500/30 text-emerald-300"
                  : "bg-rose-500/10 border-rose-500/30 text-rose-300"
              }`}
            >
              {chainVerifyResult.valid ? (
                <>
                  <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
                  <span>Chain intact: all {chainVerifyResult.chain_length} blocks mathematically verified.</span>
                </>
              ) : (
                <>
                  <AlertTriangle className="w-4 h-4 text-rose-400 shrink-0" />
                  <span>Integrity compromised at block #{chainVerifyResult.broken_at_event_id}!</span>
                </>
              )}
            </div>
          )}

          <div className="overflow-x-auto max-h-96">
            <table className="w-full text-left text-xs font-mono">
              <thead className="bg-slate-950 text-slate-400 border-b border-slate-800 font-sans sticky top-0">
                <tr>
                  <th className="py-2.5 px-3">#</th>
                  <th className="py-2.5 px-3">Event Type</th>
                  <th className="py-2.5 px-3">Timestamp</th>
                  <th className="py-2.5 px-3">Payload Summary</th>
                  <th className="py-2.5 px-3">Block Hash (SHA-256)</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {auditChain.map((ev) => (
                  <tr key={ev.event_id} className="hover:bg-slate-950/40">
                    <td className="py-2 px-3 text-slate-400">{ev.event_id}</td>
                    <td className="py-2 px-3">
                      <span className="text-cyan-400 font-semibold">{ev.event_type}</span>
                    </td>
                    <td className="py-2 px-3 text-slate-400">
                      {new Date(ev.timestamp * 1000).toLocaleTimeString()}
                    </td>
                    <td className="py-2 px-3 text-slate-300 max-w-xs truncate font-sans">
                      {JSON.stringify(ev.payload)}
                    </td>
                    <td className="py-2 px-3 text-purple-400 truncate max-w-[140px]" title={ev.current_hash}>
                      {ev.current_hash.slice(0, 16)}...
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* TOTP Step-Up Modal for Thresholds */}
      {showTotpModal && (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-rose-500/40 rounded-2xl max-w-md w-full p-6 text-slate-200 shadow-2xl">
            <div className="flex items-center gap-2 mb-2 text-rose-400">
              <ShieldAlert className="w-5 h-5" />
              <h3 className="font-bold text-white text-base">Superuser 2FA Authorization</h3>
            </div>
            <p className="text-xs text-slate-400 mb-4">
              Updating global detection thresholds alters platform-wide forensic classifications. Enter your 6-digit TOTP code to authorize:
            </p>

            <form onSubmit={handleSaveThresholds} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-2 text-center uppercase tracking-wider">
                  6-Digit Authenticator Code
                </label>
                <OtpInput
                  length={6}
                  value={totpCode}
                  onChange={setTotpCode}
                  onComplete={(code) => setTotpCode(code)}
                  disabled={savingThresholds}
                  ariaLabel="TOTP Code for Admin Thresholds"
                />
              </div>

              {/* Dev hint */}
              <div className="p-2 rounded-lg bg-slate-950 border border-slate-800 text-[11px] text-slate-400 flex items-center justify-between font-mono">
                <span>Dev Master TOTP:</span>
                <button
                  type="button"
                  onClick={() => setTotpCode("123456")}
                  className="text-rose-400 hover:text-rose-300 underline font-semibold"
                >
                  Fill "123456"
                </button>
              </div>

              <div className="flex items-center justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => {
                    setShowTotpModal(false);
                    setTotpCode("");
                  }}
                  className="px-3.5 py-2 rounded-xl bg-slate-800 text-slate-300 hover:text-white text-xs font-medium"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={totpCode.length !== 6 || savingThresholds}
                  className="px-4 py-2 rounded-xl bg-rose-600 hover:bg-rose-500 text-white text-xs font-semibold flex items-center gap-1.5 disabled:opacity-50"
                >
                  {savingThresholds ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Save className="w-3.5 h-3.5" />}
                  <span>Authorize & Save</span>
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
