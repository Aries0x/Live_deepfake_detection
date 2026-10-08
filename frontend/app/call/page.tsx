"use client";

import React, { useState, useEffect, useRef } from "react";
import { useRouter } from "next/navigation";
import {
  ShieldCheck,
  Video,
  KeyRound,
  ArrowRight,
  PlusCircle,
  Copy,
  Check,
  Camera,
  Mic,
  Sparkles,
  Wifi,
  Laptop,
} from "lucide-react";
import { getApiBase } from "@/lib/config";

export default function MeetingGatewayPage() {
  const router = useRouter();
  const [roomCode, setRoomCode] = useState("");
  const [copied, setCopied] = useState(false);
  const [previewStream, setPreviewStream] = useState<MediaStream | null>(null);
  const [videoDevices, setVideoDevices] = useState<MediaDeviceInfo[]>([]);
  const [selectedDevice, setSelectedDevice] = useState<string>("");
  const [cameraActive, setCameraActive] = useState(false);
  const previewVideoRef = useRef<HTMLVideoElement>(null);

  const [mounted, setMounted] = useState(false);
  const [localHost, setLocalHost] = useState("localhost");
  const defaultCode = "DEMO-ROOM";

  useEffect(() => {
    setMounted(true);
    if (typeof window !== "undefined") {
      setLocalHost(window.location.hostname);
    }
  }, []);

  const inviteUrl = mounted && typeof window !== "undefined"
    ? `${window.location.protocol}//${window.location.host}/call/${roomCode.trim() || defaultCode}`
    : `http://localhost:3000/call/${defaultCode}`;

  // Enumerate cameras
  useEffect(() => {
    async function loadDevices() {
      try {
        const devices = await navigator.mediaDevices.enumerateDevices();
        const vInputs = devices.filter((d) => d.kind === "videoinput");
        setVideoDevices(vInputs);
        if (vInputs.length > 0 && !selectedDevice) {
          const obsCam = vInputs.find((d) => d.label.toLowerCase().includes("obs"));
          setSelectedDevice(obsCam ? obsCam.deviceId : vInputs[0].deviceId);
        }
      } catch (e) {
        console.warn("Device enumeration:", e);
      }
    }
    loadDevices();
  }, []);

  // Pre-call preview stream
  const startPreview = async (deviceId?: string) => {
    try {
      if (previewStream) {
        previewStream.getTracks().forEach((t) => t.stop());
      }
      const constraints: MediaStreamConstraints = {
        video: deviceId ? { deviceId: { exact: deviceId } } : true,
        audio: true,
      };
      const stream = await navigator.mediaDevices.getUserMedia(constraints);
      setPreviewStream(stream);
      setCameraActive(true);
      if (previewVideoRef.current) {
        previewVideoRef.current.srcObject = stream;
      }
    } catch (err) {
      console.warn("Preview camera error:", err);
      setCameraActive(false);
    }
  };

  useEffect(() => {
    return () => {
      if (previewStream) {
        previewStream.getTracks().forEach((t) => t.stop());
      }
    };
  }, [previewStream]);

  const handleJoin = (e: React.FormEvent) => {
    e.preventDefault();
    const targetRoom = roomCode.trim() || defaultCode;
    const cleanRoom = targetRoom.toUpperCase().replace(/^(CALL-)+/g, "").replace(/[^A-Z0-9_-]/g, "");
    router.push(`/call/${cleanRoom || defaultCode}`);
  };

  const handleCreateInstant = () => {
    const randomCode = `ROOM-${Math.floor(1000 + Math.random() * 9000)}`;
    router.push(`/call/${randomCode}`);
  };

  const copyInvite = () => {
    navigator.clipboard.writeText(inviteUrl);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="max-w-6xl mx-auto px-6 py-10 space-y-10">
      {/* Header */}
      <div className="text-center space-y-3 max-w-2xl mx-auto">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-xs font-mono">
          <ShieldCheck className="w-3.5 h-3.5" /> SecureCall Forensic Gateway
        </div>
        <h1 className="text-3xl sm:text-4xl font-extrabold text-white tracking-tight">
          Join or Start a Live Forensic Call
        </h1>
        <p className="text-sm text-slate-400">
          Enter a meeting room code to connect with your colleague over local Wi-Fi with real-time deepfake detection.
        </p>
      </div>

      {/* Main Grid: Code Login Form + Camera Preview Check */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
        {/* Left Column: Code Login Form (7 Cols) */}
        <div className="lg:col-span-7 space-y-6">
          {/* Card 1: Enter Room Code Form */}
          <div className="glass-panel p-6 sm:p-8 space-y-6">
            <div className="space-y-1">
              <h2 className="text-lg font-bold text-white flex items-center gap-2">
                <KeyRound className="w-5 h-5 text-emerald-400" /> Enter Meeting Code
              </h2>
              <p className="text-xs text-slate-400">
                Type the room code provided by your peer or choose a demo room below.
              </p>
            </div>

            <form onSubmit={handleJoin} className="space-y-4">
              <div className="relative">
                <input
                  type="text"
                  value={roomCode}
                  onChange={(e) => setRoomCode(e.target.value)}
                  placeholder="e.g. DEMO-ROOM or SEC-4891"
                  className="w-full px-4 py-3.5 rounded-xl bg-slate-900/90 border border-slate-700 text-white font-mono text-base placeholder:text-slate-500 focus:outline-none focus:border-emerald-500 transition-colors uppercase tracking-wider"
                />
              </div>

              <div className="flex flex-col sm:flex-row gap-3">
                <button
                  type="submit"
                  className="flex-1 py-3.5 px-6 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-semibold text-sm flex items-center justify-center gap-2 transition-all cursor-pointer shadow-lg shadow-emerald-950/40"
                >
                  <Video className="w-4 h-4" /> Join Forensic Call <ArrowRight className="w-4 h-4" />
                </button>

                <button
                  type="button"
                  onClick={handleCreateInstant}
                  className="py-3.5 px-5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 font-medium text-sm flex items-center justify-center gap-2 transition-colors cursor-pointer"
                >
                  <PlusCircle className="w-4 h-4 text-emerald-400" /> New Code
                </button>
              </div>
            </form>

            {/* Quick Demo Presets */}
            <div className="pt-4 border-t border-slate-800/80 space-y-2">
              <span className="text-[11px] uppercase tracking-wider text-slate-400 font-semibold block">
                Quick Demo Presets
              </span>
              <div className="flex flex-wrap gap-2">
                {["DEMO-ROOM", "EXECUTIVE-CALL", "KYC-VERIFICATION"].map((preset) => (
                  <button
                    key={preset}
                    onClick={() => {
                      setRoomCode(preset);
                      router.push(`/call/${preset}`);
                    }}
                    className="px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-700/80 hover:border-emerald-500/50 hover:bg-slate-800 text-xs font-mono text-slate-300 transition-all cursor-pointer"
                  >
                    {preset}
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* Card 2: Wi-Fi Shareable Invite Link */}
          <div className="glass-panel p-6 space-y-3 border-blue-500/20 bg-blue-950/10">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2 text-xs font-semibold text-blue-300">
                <Wifi className="w-4 h-4 text-blue-400" /> Share with Friend over Wi-Fi
              </div>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-blue-500/10 text-blue-400 border border-blue-500/30">
                LAN Host: {localHost}
              </span>
            </div>

            <p className="text-xs text-slate-300">
              Your colleague on the same Wi-Fi can join directly using this link or by typing meeting code{" "}
              <strong className="text-emerald-400 font-mono">{roomCode.trim() || defaultCode}</strong>:
            </p>

            <div className="flex items-center gap-2 p-2 rounded-lg bg-slate-950 border border-slate-800">
              <input
                type="text"
                readOnly
                value={inviteUrl}
                className="flex-1 bg-transparent text-xs font-mono text-slate-300 focus:outline-none px-2 truncate"
              />
              <button
                onClick={copyInvite}
                className="px-3 py-1.5 rounded bg-blue-600 hover:bg-blue-500 text-white text-xs font-medium flex items-center gap-1.5 transition-colors cursor-pointer"
              >
                {copied ? <Check className="w-3.5 h-3.5 text-emerald-300" /> : <Copy className="w-3.5 h-3.5" />}
                {copied ? "Copied!" : "Copy Link"}
              </button>
            </div>
          </div>
        </div>

        {/* Right Column: Pre-Flight Device & OBS Virtual Cam Check (5 Cols) */}
        <div className="lg:col-span-5 space-y-6">
          <div className="glass-panel p-6 space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="font-bold text-white text-sm flex items-center gap-2">
                <Camera className="w-4 h-4 text-emerald-400" /> Pre-Flight Camera Check
              </h3>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-400">
                Hardware Preview
              </span>
            </div>

            {/* Video Preview Box */}
            <div className="relative aspect-video rounded-xl bg-slate-950 border border-slate-800 overflow-hidden flex items-center justify-center">
              <video
                ref={previewVideoRef}
                autoPlay
                playsInline
                muted
                className={`w-full h-full object-cover ${!cameraActive ? "hidden" : ""}`}
              />

              {!cameraActive && (
                <div className="text-center p-6 space-y-2">
                  <div className="w-12 h-12 rounded-full bg-slate-900 border border-slate-800 flex items-center justify-center mx-auto text-slate-500">
                    <Camera className="w-6 h-6" />
                  </div>
                  <p className="text-xs text-slate-400">Click below to test your camera before joining</p>
                  <button
                    onClick={() => startPreview(selectedDevice)}
                    className="px-3 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-medium cursor-pointer"
                  >
                    Test Webcam / OBS Virtual Cam
                  </button>
                </div>
              )}

              {cameraActive && (
                <div className="absolute bottom-2 left-2 px-2 py-0.5 rounded bg-black/70 text-[10px] font-mono text-emerald-400 border border-emerald-500/30">
                  Preview Active
                </div>
              )}
            </div>

            {/* Camera Selector Dropdown */}
            {videoDevices.length > 0 && (
              <div className="space-y-1">
                <label className="text-[11px] text-slate-400 font-medium">Select Video Device:</label>
                <select
                  value={selectedDevice}
                  onChange={(e) => {
                    setSelectedDevice(e.target.value);
                    if (cameraActive) startPreview(e.target.value);
                  }}
                  className="w-full px-3 py-2 rounded-lg bg-slate-900 border border-slate-700 text-xs text-slate-200 focus:outline-none"
                >
                  {videoDevices.map((d, i) => {
                    const isObs = (d.label || "").toLowerCase().includes("obs");
                    return (
                      <option key={d.deviceId || i} value={d.deviceId}>
                        {isObs ? `🎥 ${d.label} (OBS)` : d.label || `Camera ${i + 1}`}
                      </option>
                    );
                  })}
                </select>
              </div>
            )}

            {/* OBS Quick Help */}
            <div className="p-3 rounded-lg bg-slate-900/80 border border-slate-800 space-y-2 text-xs">
              <span className="font-semibold text-slate-300 block text-[11px]">
                Attacker / Friend OBS Instructions:
              </span>
              <ol className="list-decimal list-inside space-y-1 text-slate-400 text-[11px]">
                <li>Open OBS Studio $\rightarrow$ Sources (+) $\rightarrow$ Media Source</li>
                <li>Pick deepfake MP4 and check <strong>Loop</strong></li>
                <li>Click <strong>Start Virtual Camera</strong> in OBS</li>
                <li>Select <strong>OBS Virtual Camera</strong> in the dropdown</li>
              </ol>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
