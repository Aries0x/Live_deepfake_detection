"use client";

import React, { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  ShieldCheck,
  Lock,
  Mail,
  KeyRound,
  ArrowRight,
  Loader2,
  AlertCircle,
  ShieldAlert,
  Terminal,
  CheckCircle2,
  Info,
} from "lucide-react";
import OtpInput from "@/components/auth/OtpInput";
import { getApiBase } from "@/lib/config";
import { setStoredToken } from "@/lib/auth";

export default function UnifiedLoginPage() {
  const router = useRouter();

  // Step 1: Identifier + Password (or OTP); Step 2: 2FA TOTP
  const [step, setStep] = useState<1 | 2>(1);
  const [identifier, setIdentifier] = useState("");
  const [password, setPassword] = useState("");
  const [pendingToken, setPendingToken] = useState<string | null>(null);
  const [totpCode, setTotpCode] = useState("");
  const [roleDetected, setRoleDetected] = useState<string | null>(null);

  // States
  const [isLoading, setIsLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState("");
  const [isLockedOut, setIsLockedOut] = useState(false);

  // Step 1: Submit Credentials
  const handleLoginSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!identifier.trim()) {
      setErrorMsg("Please enter your registered email or phone number.");
      return;
    }

    setIsLoading(true);
    setErrorMsg("");

    try {
      const res = await fetch(`${getApiBase()}/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({
          identifier: identifier.trim(),
          password: password || "Demo@1234",
        }),
      });

      const data = await res.json();
      if (!res.ok) {
        if (res.status === 429) {
          setIsLockedOut(true);
          setErrorMsg(data.detail || "Too many attempts. Account locked for 5 minutes.");
        } else {
          setErrorMsg(data.detail || "Invalid email or password. Please verify your credentials.");
        }
        return;
      }

      // If Privileged Role (Court Officer, Judge, Admin) -> requires 2FA
      if (data.requires_2fa && data.pending_token) {
        setPendingToken(data.pending_token);
        setRoleDetected(data.role);
        setStep(2);
        return;
      }

      // Store session token if provided
      if (data.token) {
        setStoredToken(data.token);
      }

      // If Citizen -> Direct login without 2FA!
      if (data.role === "citizen") {
        router.push("/dashboard/citizen");
      } else if (data.role === "forensic_officer") {
        router.push("/dashboard/forensic");
      } else {
        router.push(`/dashboard/${data.role}`);
      }
    } catch {
      setErrorMsg("Unable to contact authentication server. Check network connection.");
    } finally {
      setIsLoading(false);
    }
  };

  // Step 2: Verify TOTP 2FA
  const handleVerify2FA = async (code: string) => {
    if (!pendingToken) {
      setErrorMsg("Session missing or expired. Please re-enter credentials.");
      setStep(1);
      return;
    }

    setIsLoading(true);
    setErrorMsg("");

    try {
      const res = await fetch(`${getApiBase()}/auth/verify-2fa`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({
          pending_token: pendingToken,
          totp_code: code,
        }),
      });

      const data = await res.json();
      if (!res.ok) {
        if (res.status === 429) {
          setIsLockedOut(true);
          setErrorMsg(data.detail || "Too many attempts. Account locked.");
        } else {
          setErrorMsg(data.detail || "Invalid 2FA code. Please verify authenticator.");
        }
        return;
      }

      if (data.token) {
        setStoredToken(data.token);
      }

      // Route strictly according to user's assigned role
      switch (data.role) {
        case "forensic_officer":
          router.push("/dashboard/forensic");
          break;
        case "judge":
          router.push("/dashboard/judge");
          break;
        case "admin":
          router.push("/dashboard/admin");
          break;
        default:
          router.push("/dashboard/citizen");
          break;
      }
    } catch {
      setErrorMsg("Error verifying TOTP code. Please try again.");
    } finally {
      setIsLoading(false);
    }
  };

  // Quick-fill presets
  const applyPreset = (presetId: string, emailVal: string) => {
    setIdentifier(emailVal);
    setPassword("Demo@1234");
    setErrorMsg("");
  };

  return (
    <div className="min-h-[calc(100vh-65px)] flex items-center justify-center p-4 sm:p-6 lg:p-8 bg-radial-gradient">
      <div className="w-full max-w-md bg-slate-900/90 border border-slate-800 rounded-3xl p-6 sm:p-8 backdrop-blur-2xl shadow-2xl relative overflow-hidden">
        {/* Glow Top Accent */}
        <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-cyan-500 via-amber-400 to-rose-500" />

        {/* Brand Header */}
        <div className="text-center mb-8">
          <div className="inline-flex p-3 rounded-2xl bg-slate-950 border border-slate-800 text-cyan-400 mb-3 shadow-inner">
            <ShieldCheck className="w-8 h-8 text-cyan-400" />
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
            SecureCall Portal
          </h1>
          <p className="text-xs text-slate-400 mt-1 max-w-xs mx-auto">
            Real-time deepfake protection. Court-grade forensic verification.
          </p>
        </div>

        {/* Error Alert */}
        {errorMsg && (
          <div
            role="alert"
            aria-live="assertive"
            className={`p-3.5 rounded-xl border text-xs mb-5 flex items-start gap-2.5 ${
              isLockedOut
                ? "border-rose-500/40 bg-rose-950/40 text-rose-300"
                : "border-red-500/30 bg-red-950/40 text-red-300"
            }`}
          >
            {isLockedOut ? (
              <Lock className="w-4 h-4 text-rose-400 shrink-0 mt-0.5" />
            ) : (
              <AlertCircle className="w-4 h-4 text-red-400 shrink-0 mt-0.5" />
            )}
            <span>{errorMsg}</span>
          </div>
        )}

        {/* Step 1: Single Unified Credentials Form */}
        {step === 1 && (
          <form onSubmit={handleLoginSubmit} className="space-y-4">
            {/* Quick Demo Credentials Bar */}
            <div className="p-3 rounded-2xl bg-slate-950/70 border border-slate-800 space-y-2">
              <div className="flex items-center justify-between text-[11px] text-slate-400 font-semibold">
                <span className="flex items-center gap-1">
                  <Terminal className="w-3.5 h-3.5 text-cyan-400" /> Quick Account Fill:
                </span>
                <span className="text-[10px] text-slate-500">Auto-detects role</span>
              </div>
              <div className="grid grid-cols-2 gap-1.5 text-xs font-mono">
                <button
                  id="fill-citizen-chip"
                  type="button"
                  onClick={() => applyPreset("citizen", "citizen@demo.com")}
                  className="px-2.5 py-1.5 rounded-lg bg-slate-900 hover:bg-slate-800 text-cyan-300 border border-slate-800 text-left truncate transition-colors"
                >
                  Citizen
                </button>
                <button
                  id="fill-forensic-chip"
                  type="button"
                  onClick={() => applyPreset("forensic", "officer@court.demo")}
                  className="px-2.5 py-1.5 rounded-lg bg-slate-900 hover:bg-slate-800 text-amber-300 border border-slate-800 text-left truncate transition-colors"
                >
                  Forensic Verificator
                </button>
                <button
                  id="fill-judge-chip"
                  type="button"
                  onClick={() => applyPreset("judge", "judge@court.demo")}
                  className="px-2.5 py-1.5 rounded-lg bg-slate-900 hover:bg-slate-800 text-amber-300 border border-slate-800 text-left truncate transition-colors"
                >
                  Court Judge
                </button>
                <button
                  id="fill-admin-chip"
                  type="button"
                  onClick={() => applyPreset("admin", "admin@securecall.demo")}
                  className="px-2.5 py-1.5 rounded-lg bg-slate-900 hover:bg-slate-800 text-rose-300 border border-slate-800 text-left truncate transition-colors"
                >
                  Administrator
                </button>
              </div>
            </div>

            {/* Identifier (Email / Phone) */}
            <div>
              <label
                htmlFor="unified-identifier"
                className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1.5"
              >
                Email or Username
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-500">
                  <Mail className="w-4 h-4" />
                </div>
                <input
                  id="unified-identifier"
                  type="text"
                  required
                  autoComplete="username email"
                  disabled={isLoading || isLockedOut}
                  placeholder="e.g. officer@court.demo or citizen@demo.com"
                  value={identifier}
                  onChange={(e) => setIdentifier(e.target.value)}
                  className="w-full pl-10 pr-4 py-2.5 rounded-xl bg-slate-950/80 border border-slate-700 text-white placeholder-slate-500 text-sm focus:outline-none focus:border-cyan-400 focus:ring-1 focus:ring-cyan-400 transition-colors"
                />
              </div>
            </div>

            {/* Password */}
            <div>
              <label
                htmlFor="unified-password"
                className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1.5"
              >
                Password
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-500">
                  <Lock className="w-4 h-4" />
                </div>
                <input
                  id="unified-password"
                  type="password"
                  autoComplete="current-password"
                  disabled={isLoading || isLockedOut}
                  placeholder="••••••••••••"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full pl-10 pr-4 py-2.5 rounded-xl bg-slate-950/80 border border-slate-700 text-white placeholder-slate-500 text-sm focus:outline-none focus:border-cyan-400 focus:ring-1 focus:ring-cyan-400 transition-colors"
                />
              </div>
              <p className="text-[11px] text-slate-500 mt-1">
                Your role and access rights are automatically determined by your account profile.
              </p>
            </div>

            <button
              id="unified-login-submit"
              type="submit"
              disabled={isLoading || isLockedOut || !identifier.trim()}
              className="w-full py-3 px-4 rounded-xl font-medium text-sm text-white bg-gradient-to-r from-cyan-600 via-teal-600 to-emerald-600 hover:from-cyan-500 hover:to-emerald-500 shadow-lg shadow-cyan-950/50 transition-all flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed pt-3"
            >
              {isLoading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>Authenticating...</span>
                </>
              ) : (
                <>
                  <span>Sign In</span>
                  <ArrowRight className="w-4 h-4" />
                </>
              )}
            </button>
          </form>
        )}

        {/* Step 2: Mandatory 2FA TOTP Form for Privileged Roles */}
        {step === 2 && (
          <div className="space-y-5">
            <div className="text-center">
              <div className="inline-flex p-3 rounded-2xl bg-amber-500/10 border border-amber-500/30 text-amber-400 mb-2">
                <KeyRound className="w-7 h-7" />
              </div>
              <h2 className="text-lg font-bold text-white">Two-Factor Authentication</h2>
              <p className="text-xs text-slate-400 mt-0.5">
                Role: <strong className="text-amber-400 font-mono uppercase">{roleDetected?.replace("_", " ")}</strong>
              </p>
            </div>

            {/* Audit Chain Warning */}
            <div className="p-3 rounded-xl border border-amber-500/20 bg-amber-500/10 text-amber-300 text-xs flex items-start gap-2.5">
              <ShieldAlert className="w-4 h-4 shrink-0 mt-0.5" />
              <span className="text-[11px] leading-relaxed">
                Court & administrative access is cryptographically anchored to the SHA-256 hash custody chain.
              </span>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-3 text-center uppercase tracking-wider">
                6-Digit Authenticator Code
              </label>
              <OtpInput
                length={6}
                value={totpCode}
                onChange={setTotpCode}
                onComplete={(code) => handleVerify2FA(code)}
                disabled={isLoading || isLockedOut}
                ariaLabel="6-Digit TOTP Two-Factor Authentication Code"
              />
            </div>

            {/* Dev Quick-Fill */}
            <div className="p-2 rounded-lg bg-slate-950 border border-slate-800 text-[11px] text-slate-400 flex items-center justify-between font-mono">
              <span>Dev Master Code:</span>
              <button
                id="btn-fill-totp-master"
                type="button"
                onClick={() => {
                  setTotpCode("123456");
                  handleVerify2FA("123456");
                }}
                className="text-amber-400 hover:text-amber-300 underline font-semibold"
              >
                Fill "123456"
              </button>
            </div>

            <button
              id="totp-verify-submit"
              type="button"
              onClick={() => handleVerify2FA(totpCode)}
              disabled={totpCode.length !== 6 || isLoading || isLockedOut}
              className="w-full py-3 px-4 rounded-xl font-medium text-sm text-white bg-amber-600 hover:bg-amber-500 shadow-lg shadow-amber-950/40 transition-all flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isLoading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>Verifying Token...</span>
                </>
              ) : (
                <>
                  <CheckCircle2 className="w-4 h-4" />
                  <span>Verify & Enter Console</span>
                </>
              )}
            </button>

            <button
              type="button"
              onClick={() => {
                setStep(1);
                setTotpCode("");
                setErrorMsg("");
              }}
              className="w-full py-2 text-xs text-slate-400 hover:text-slate-200 transition-colors"
            >
              ← Back to credentials
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
