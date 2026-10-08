"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  Video,
  ShieldCheck,
  PhoneCall,
  Download,
  Clock,
  ArrowRight,
  LogOut,
  User,
  CheckCircle2,
  AlertTriangle,
  Loader2,
  FileCheck,
} from "lucide-react";
import { getMe, logout, can, UserSession } from "@/lib/auth";
import { getApiBase } from "@/lib/config";

export default function CitizenDashboardPage() {
  const router = useRouter();
  const [user, setUser] = useState<UserSession | null>(null);
  const [loading, setLoading] = useState(true);
  const [joinRoomId, setJoinRoomId] = useState("");
  const [customRoomId, setCustomRoomId] = useState(`call-${Math.floor(1000 + Math.random() * 9000)}`);

  // Mock citizen call history
  const [callHistory] = useState([
    {
      id: "CALL-CZ-8921",
      room: "interview-tech-screening",
      date: "Today, 14:22",
      duration: "18m 42s",
      risk: "9.4%",
      verdict: "LIKELY_AUTHENTIC",
    },
    {
      id: "CALL-CZ-7104",
      room: "family-checkin",
      date: "Yesterday, 19:05",
      duration: "08m 15s",
      risk: "12.1%",
      verdict: "LIKELY_AUTHENTIC",
    },
    {
      id: "CALL-CZ-6420",
      room: "urgent-banking-verify",
      date: "Oct 01, 11:30",
      duration: "03m 10s",
      risk: "86.5%",
      verdict: "SUSPECT_MANIPULATION",
    },
  ]);

  const [accessDeniedToast, setAccessDeniedToast] = useState(false);

  useEffect(() => {
    if (typeof window !== "undefined") {
      const params = new URLSearchParams(window.location.search);
      if (params.get("access_denied")) {
        setAccessDeniedToast(true);
        const timer = setTimeout(() => setAccessDeniedToast(false), 6000);
        return () => clearTimeout(timer);
      }
    }
  }, []);

  useEffect(() => {
    getMe().then((u) => {
      if (!u) {
        router.push("/login/citizen");
      } else {
        setUser(u);
      }
      setLoading(false);
    });
  }, [router]);

  if (loading) {
    return (
      <div className="min-h-[calc(100vh-65px)] flex items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-cyan-400" />
      </div>
    );
  }

  if (!user) return null;

  const canJoin = can(user, "live_call.join");
  const canDownloadReport = can(user, "live_call.download_report");

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {/* Access Denied Toast */}
      {accessDeniedToast && (
        <div
          role="alert"
          aria-live="assertive"
          className="p-4 rounded-xl border border-rose-500/40 bg-rose-950/80 text-rose-200 text-xs flex items-center justify-between shadow-2xl backdrop-blur-md animate-fade-in"
        >
          <div className="flex items-center gap-3">
            <AlertTriangle className="w-5 h-5 text-rose-400 shrink-0" />
            <span className="font-semibold text-sm">You don't have access to that page.</span>
            <span className="text-slate-300">Court and bulk verification tools require authorized judicial credentials.</span>
          </div>
          <button
            onClick={() => setAccessDeniedToast(false)}
            className="text-rose-400 hover:text-white text-xs px-2 py-1 rounded bg-rose-900/40 hover:bg-rose-900/80"
          >
            Dismiss
          </button>
        </div>
      )}

      {/* Header Banner */}
      <div className="bg-gradient-to-r from-slate-900 via-slate-900 to-cyan-950/40 border border-cyan-500/20 rounded-2xl p-6 sm:p-8 backdrop-blur-xl shadow-xl flex flex-col md:flex-row md:items-center justify-between gap-6">
        <div>
          <div className="flex items-center gap-2 mb-2">
            <span className="text-xs font-mono font-semibold uppercase tracking-wider px-2.5 py-1 rounded-full bg-cyan-500/10 text-cyan-400 border border-cyan-500/30">
              CITIZEN SUITE
            </span>
            <span className="text-xs font-medium px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 flex items-center gap-1">
              <CheckCircle2 className="w-3 h-3" /> Biometric Consent Active
            </span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-white">
            Welcome back, {user.name || "Citizen User"}
          </h1>
          <p className="text-xs sm:text-sm text-slate-400 mt-1 max-w-xl">
            Real-time biometric protection for personal and professional calls. High-frequency facial & voice deepfake detection.
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

      {/* Main Action Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Start Protected Call Card */}
        <div className="bg-slate-900/80 border border-cyan-500/30 rounded-2xl p-6 shadow-xl flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-4">
              <div className="p-3 rounded-xl bg-cyan-500/10 border border-cyan-500/30 text-cyan-400">
                <Video className="w-6 h-6" />
              </div>
              <span className="text-xs font-semibold text-cyan-400 bg-cyan-950/60 px-2.5 py-1 rounded-full border border-cyan-800">
                Live Forensics HUD
              </span>
            </div>
            <h2 className="text-xl font-bold text-white mb-2">Start Protected Call</h2>
            <p className="text-xs text-slate-300 leading-relaxed mb-6">
              Launch a secure WebRTC room. Continuous facial manipulation, voice clone anti-spoofing, and temporal consistency detection will run in real-time.
            </p>

            <div className="space-y-2 mb-6">
              <label className="block text-xs font-semibold text-slate-400 uppercase">Room ID</label>
              <input
                type="text"
                value={customRoomId}
                onChange={(e) => setCustomRoomId(e.target.value)}
                className="w-full px-3.5 py-2.5 rounded-xl bg-slate-950 border border-slate-700 text-white text-xs font-mono focus:outline-none focus:border-cyan-400"
              />
            </div>
          </div>

          {canJoin ? (
            <Link
              href={`/call/${encodeURIComponent(customRoomId)}`}
              className="w-full py-3 px-4 rounded-xl font-medium text-sm text-white bg-gradient-to-r from-cyan-600 to-teal-600 hover:from-cyan-500 hover:to-teal-500 shadow-lg shadow-cyan-950/50 flex items-center justify-center gap-2 transition-all"
            >
              <Video className="w-4 h-4" />
              <span>Launch Protected Call</span>
            </Link>
          ) : (
            <button
              disabled
              className="w-full py-3 px-4 rounded-xl font-medium text-sm text-slate-500 bg-slate-800 border border-slate-700 cursor-not-allowed"
            >
              Call Join Permission Missing
            </button>
          )}
        </div>

        {/* Join Call Card */}
        <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 shadow-xl flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-4">
              <div className="p-3 rounded-xl bg-slate-800 border border-slate-700 text-slate-300">
                <PhoneCall className="w-6 h-6" />
              </div>
              <span className="text-xs font-semibold text-slate-400 bg-slate-800/80 px-2.5 py-1 rounded-full border border-slate-700">
                Peer-to-Peer
              </span>
            </div>
            <h2 className="text-xl font-bold text-white mb-2">Join Existing Call</h2>
            <p className="text-xs text-slate-300 leading-relaxed mb-6">
              Enter a room code provided by another participant to join an active call with full forensic HUD monitoring.
            </p>

            <div className="space-y-2 mb-6">
              <label className="block text-xs font-semibold text-slate-400 uppercase">Enter Room Code</label>
              <input
                type="text"
                placeholder="e.g. demo-room or call-4821"
                value={joinRoomId}
                onChange={(e) => setJoinRoomId(e.target.value)}
                className="w-full px-3.5 py-2.5 rounded-xl bg-slate-950 border border-slate-700 text-white text-xs font-mono focus:outline-none focus:border-cyan-400"
              />
            </div>
          </div>

          <button
            onClick={() => {
              if (joinRoomId.trim()) {
                router.push(`/call/${encodeURIComponent(joinRoomId.trim())}`);
              }
            }}
            disabled={!joinRoomId.trim() || !canJoin}
            className="w-full py-3 px-4 rounded-xl font-medium text-sm text-white bg-slate-800 hover:bg-slate-700 border border-slate-700 transition-all flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <span>Connect to Room</span>
            <ArrowRight className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Citizen Past Calls and Reports Table */}
      <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-bold text-white flex items-center gap-2">
              <Clock className="w-5 h-5 text-cyan-400" /> My Call History & Forensic Reports
            </h3>
            <p className="text-xs text-slate-400">
              Only your authenticated calls are listed. Reports are cryptographically signed.
            </p>
          </div>
          <span className="text-xs font-mono text-cyan-400 bg-cyan-950/40 px-3 py-1 rounded-full border border-cyan-800">
            {callHistory.length} Sessions Logged
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-950/80 text-slate-400 border-b border-slate-800">
              <tr>
                <th className="py-3 px-4">Session ID</th>
                <th className="py-3 px-4">Room Name</th>
                <th className="py-3 px-4">Timestamp</th>
                <th className="py-3 px-4">Duration</th>
                <th className="py-3 px-4">Peak Risk</th>
                <th className="py-3 px-4">Integrity Status</th>
                <th className="py-3 px-4 text-right">Report</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 font-mono">
              {callHistory.map((call) => (
                <tr key={call.id} className="hover:bg-slate-950/40 transition-colors">
                  <td className="py-3 px-4 font-bold text-white">{call.id}</td>
                  <td className="py-3 px-4 text-slate-300 font-sans">{call.room}</td>
                  <td className="py-3 px-4 text-slate-400">{call.date}</td>
                  <td className="py-3 px-4 text-slate-400">{call.duration}</td>
                  <td className="py-3 px-4 font-bold text-white">{call.risk}</td>
                  <td className="py-3 px-4">
                    <span
                      className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                        call.verdict === "SUSPECT_MANIPULATION"
                          ? "bg-rose-500/20 text-rose-400 border border-rose-500/30"
                          : "bg-emerald-500/20 text-emerald-400 border border-emerald-500/30"
                      }`}
                    >
                      {call.verdict.replace("_", " ")}
                    </span>
                  </td>
                  <td className="py-3 px-4 text-right">
                    {canDownloadReport ? (
                      <div className="inline-flex items-center gap-2">
                        <a
                          href={`${getApiBase()}/api/v1/calls/${call.id}/report?format=pdf`}
                          target="_blank"
                          rel="noreferrer"
                          className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded bg-indigo-600/20 hover:bg-indigo-600/30 text-indigo-400 hover:text-indigo-300 border border-indigo-500/30 text-xs font-sans font-medium transition-colors"
                        >
                          <Download className="w-3.5 h-3.5" />
                          <span>PDF</span>
                        </a>
                        <a
                          href={`${getApiBase()}/api/v1/calls/${call.id}/report?format=html`}
                          target="_blank"
                          rel="noreferrer"
                          className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-cyan-400 hover:text-cyan-300 border border-slate-700 text-xs font-sans font-medium transition-colors"
                        >
                          <Download className="w-3.5 h-3.5" />
                          <span>HTML</span>
                        </a>
                      </div>
                    ) : (
                      <span className="text-slate-600">Restricted</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
