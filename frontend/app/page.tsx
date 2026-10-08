"use client";

import React, { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  ShieldAlert,
  Video,
  Layers,
  Cpu,
  Fingerprint,
  FileCheck2,
  Lock,
  ArrowRight,
  Zap,
  Eye,
  Mic,
  Activity,
} from "lucide-react";

export default function HomePage() {
  const router = useRouter();
  const [roomId, setRoomId] = useState("demo-room");

  const handleJoinCall = (e: React.FormEvent) => {
    e.preventDefault();
    if (roomId.trim()) {
      router.push(`/call/${encodeURIComponent(roomId.trim())}`);
    }
  };

  const scenarios = [
    { id: "A", title: "Authentic Call", desc: "Real video & speech. Expected: LOW RISK", color: "emerald" },
    { id: "B", title: "Face-Swap Attack", desc: "Manipulated video stream. Expected: Visual anomaly", color: "amber" },
    { id: "C", title: "Voice Clone Attack", desc: "Synthetic speech injection. Expected: Acoustic anomaly", color: "amber" },
    { id: "D", title: "Multimodal Deepfake", desc: "Face-swap + cloned audio. Expected: HIGH RISK", color: "rose" },
    { id: "E", title: "A/V Desync Anomaly", desc: "Mouth motion vs audio timing lag. Expected: Sync anomaly", color: "blue" },
    { id: "F", title: "Tamper Audit Check", desc: "Cryptographic hash chain verification. Expected: Validated trail", color: "purple" },
  ];

  return (
    <div className="max-w-7xl mx-auto px-6 py-12 space-y-16">
      {/* Hero Section */}
      <div className="text-center max-w-3xl mx-auto space-y-6">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-xs font-semibold uppercase tracking-wider">
          <Zap className="w-3.5 h-3.5" /> Hardware-Accelerated Defense (RTX 5050 GPU)
        </div>
        <h1 className="text-4xl sm:text-5xl font-extrabold tracking-tight text-white leading-tight">
          Real-Time Multimodal <br />
          <span className="bg-gradient-to-r from-emerald-400 via-teal-300 to-blue-500 bg-clip-text text-transparent">
            Live Call Media Integrity
          </span>
        </h1>
        <p className="text-slate-400 text-base sm:text-lg leading-relaxed">
          Defensive media forensics platform continuously monitoring live WebRTC video & audio streams.
          Correlates facial anomalies, synthetic voices, mouth synchronization, and provides verifiable tamper-evident audit trails.
        </p>

        {/* Enter Room Form */}
        <form onSubmit={handleJoinCall} className="flex flex-col sm:flex-row items-center justify-center gap-3 pt-4">
          <div className="relative w-full sm:w-80">
            <input
              type="text"
              value={roomId}
              onChange={(e) => setRoomId(e.target.value)}
              placeholder="Enter Room ID..."
              className="w-full px-4 py-3 rounded-lg bg-slate-900 border border-slate-700 text-white placeholder-slate-500 focus:outline-none focus:border-emerald-500 font-mono text-sm"
            />
          </div>
          <button
            type="submit"
            className="w-full sm:w-auto px-6 py-3 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white font-medium text-sm flex items-center justify-center gap-2 shadow-lg shadow-emerald-900/30 transition-all cursor-pointer"
          >
            <Video className="w-4 h-4" /> Start Verified Call
          </button>
        </form>
      </div>

      {/* Core Innovation Highlights */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="glass-panel p-6 space-y-3">
          <div className="p-2.5 w-fit rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-emerald-400">
            <Eye className="w-5 h-5" />
          </div>
          <h3 className="font-semibold text-lg text-white">Visual & Temporal Forensics</h3>
          <p className="text-sm text-slate-400 leading-relaxed">
            EfficientNet-B0 facial manipulation detector with Grad-CAM attribution heatmaps, face tracking, and rolling GRU temporal continuity analysis.
          </p>
        </div>

        <div className="glass-panel p-6 space-y-3">
          <div className="p-2.5 w-fit rounded-lg bg-blue-500/10 border border-blue-500/20 text-blue-400">
            <Mic className="w-5 h-5" />
          </div>
          <h3 className="font-semibold text-lg text-white">Acoustic & A/V Lip Sync</h3>
          <p className="text-sm text-slate-400 leading-relaxed">
            AASIST-L convolutional-recurrent audio anti-spoofing engine detecting synthetic voice clones paired with mouth landmark cross-correlation.
          </p>
        </div>

        <div className="glass-panel p-6 space-y-3">
          <div className="p-2.5 w-fit rounded-lg bg-purple-500/10 border border-purple-500/20 text-purple-400">
            <Lock className="w-5 h-5" />
          </div>
          <h3 className="font-semibold text-lg text-white">Tamper-Evident Audit Chain</h3>
          <p className="text-sm text-slate-400 leading-relaxed">
            Forward SHA-256 cryptographic chaining logging every frame, audio anomaly, and risk escalation to prevent post-facto evidence manipulation.
          </p>
        </div>
      </div>

      {/* Controlled Hackathon Demonstration Scenarios */}
      <div className="glass-panel p-8 space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800 pb-4">
          <div>
            <h2 className="text-xl font-bold text-white">Controlled Attack Demonstration Scenarios</h2>
            <p className="text-sm text-slate-400">
              Preset test fixtures adhering to authorized consent-based evaluation protocol.
            </p>
          </div>
          <Link
            href="/bulk"
            className="text-xs font-medium text-emerald-400 hover:text-emerald-300 flex items-center gap-1.5"
          >
            Run Offline Dataset Benchmark <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {scenarios.map((sc) => (
            <div
              key={sc.id}
              onClick={() => router.push(`/call/scenario-${sc.id.toLowerCase()}`)}
              className="p-4 rounded-lg bg-slate-900/60 border border-slate-800 hover:border-slate-700 transition-all cursor-pointer group"
            >
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-mono font-bold px-2 py-0.5 rounded bg-slate-800 text-slate-300">
                  Scenario {sc.id}
                </span>
                <span className="text-xs text-slate-500 group-hover:text-emerald-400 flex items-center gap-1">
                  Launch <ArrowRight className="w-3 h-3" />
                </span>
              </div>
              <h4 className="font-medium text-white text-sm group-hover:text-emerald-300 transition-colors">
                {sc.title}
              </h4>
              <p className="text-xs text-slate-400 mt-1">{sc.desc}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
