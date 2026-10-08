"use client";

import React, { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Scale, ArrowLeft, ArrowRight, Loader2, AlertCircle, Lock, ShieldAlert, KeyRound, Info } from "lucide-react";
import TwoFactorStep from "@/components/auth/TwoFactorStep";
import { getApiBase } from "@/lib/config";
import { setStoredToken } from "@/lib/auth";

export default function CourtLoginPage() {
  const router = useRouter();

  // Step 1: Credentials & Role Selector; Step 2: 2FA TOTP
  const [step, setStep] = useState<1 | 2>(1);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [role, setRole] = useState<"forensic_officer" | "judge">("forensic_officer");
  const [pendingToken, setPendingToken] = useState<string | null>(null);

  // States
  const [isLoading, setIsLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState("");
  const [isLockedOut, setIsLockedOut] = useState(false);

  // Step 1: Submit Credentials
  const handleCredentialSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email.trim() || !password) {
      setErrorMsg("Please enter both email and password.");
      return;
    }

    setIsLoading(true);
    setErrorMsg("");

    try {
      const res = await fetch(`${getApiBase()}/auth/court/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          email: email.trim(),
          password,
          role,
        }),
      });

      const data = await res.json();
      if (!res.ok) {
        if (res.status === 429) {
          setIsLockedOut(true);
          setErrorMsg(data.detail || "Too many attempts. Try again in 5 minutes.");
        } else {
          setErrorMsg(data.detail || "Authentication failed. Check credentials and role.");
        }
        return;
      }

      // Step 2 required
      if (data.requires_2fa && data.pending_token) {
        setPendingToken(data.pending_token);
        setStep(2);
      }
    } catch {
      setErrorMsg("Unable to contact authentication server. Check network connection.");
    } finally {
      setIsLoading(false);
    }
  };

  // Step 2: Verify TOTP 2FA
  const handleTotpVerify = async (totpCode: string) => {
    if (!pendingToken) {
      setErrorMsg("Session missing or expired. Please re-enter credentials.");
      setStep(1);
      return;
    }

    setIsLoading(true);
    setErrorMsg("");

    try {
      const res = await fetch(`${getApiBase()}/auth/court/verify-2fa`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({
          pending_token: pendingToken,
          totp_code: totpCode,
        }),
      });

      const data = await res.json();
      if (!res.ok) {
        if (res.status === 429) {
          setIsLockedOut(true);
          setErrorMsg(data.detail || "Too many attempts. Try again in 5 minutes.");
        } else {
          setErrorMsg(data.detail || "Invalid TOTP authentication code.");
        }
        return;
      }

      if (data.token) {
        setStoredToken(data.token);
      }

      // Route according to role
      const userRole = data.role || data.user?.role || role;
      if (userRole === "judge") {
        router.push("/dashboard/judge");
      } else {
        router.push("/dashboard/forensic");
      }
    } catch {
      setErrorMsg("Error verifying TOTP code. Please try again.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-[calc(100vh-65px)] flex items-center justify-center p-4 sm:p-6 lg:p-8">
      <div className="w-full max-w-md bg-slate-900/90 border border-amber-500/30 rounded-2xl p-6 sm:p-8 backdrop-blur-xl shadow-2xl relative overflow-hidden">
        {/* Glow accent */}
        <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-amber-500 via-yellow-400 to-amber-600" />

        {/* Back Link */}
        <div className="mb-6">
          <Link
            href="/login"
            className="inline-flex items-center gap-1.5 text-xs text-slate-400 hover:text-amber-400 transition-colors"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            <span>Back to Portal Roles</span>
          </Link>
        </div>

        {step === 1 ? (
          <>
            {/* Icon & Heading */}
            <div className="text-center mb-6">
              <div className="inline-flex p-3 rounded-2xl bg-amber-500/10 border border-amber-500/30 text-amber-400 mb-3 shadow-inner">
                <Scale className="w-8 h-8" />
              </div>
              <h1 className="text-2xl font-bold text-white tracking-tight">Court Forensic Portal</h1>
              <p className="text-xs text-slate-400 mt-1">
                Authorized Judicial & Evidence Verification Access
              </p>
            </div>

            {/* Note: No open signup */}
            <div className="p-3 rounded-xl bg-slate-950/70 border border-slate-800 text-[11px] text-slate-400 mb-6 flex items-start gap-2">
              <Info className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
              <span>
                Court accounts are created by the SecureCall administrator after verification. No self-registration permitted.
              </span>
            </div>

            {/* Error Message */}
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

            <form onSubmit={handleCredentialSubmit} className="space-y-4">
              {/* Role Selector */}
              <div>
                <label
                  htmlFor="court-role-select"
                  className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2"
                >
                  Court Role
                </label>
                <div className="grid grid-cols-2 gap-2">
                  <button
                    id="role-btn-officer"
                    type="button"
                    onClick={() => setRole("forensic_officer")}
                    className={`py-2 px-3 rounded-xl text-xs font-medium border transition-all ${
                      role === "forensic_officer"
                        ? "bg-amber-500/20 text-amber-300 border-amber-500/50 shadow-inner"
                        : "bg-slate-950/60 text-slate-400 border-slate-800 hover:text-slate-200"
                    }`}
                  >
                    Forensic Officer
                  </button>
                  <button
                    id="role-btn-judge"
                    type="button"
                    onClick={() => setRole("judge")}
                    className={`py-2 px-3 rounded-xl text-xs font-medium border transition-all ${
                      role === "judge"
                        ? "bg-amber-500/20 text-amber-300 border-amber-500/50 shadow-inner"
                        : "bg-slate-950/60 text-slate-400 border-slate-800 hover:text-slate-200"
                    }`}
                  >
                    Court Judge
                  </button>
                </div>
              </div>

              {/* Email */}
              <div>
                <label
                  htmlFor="court-email"
                  className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1.5"
                >
                  Official Court Email
                </label>
                <input
                  id="court-email"
                  type="email"
                  required
                  autoComplete="email"
                  disabled={isLoading || isLockedOut}
                  placeholder="e.g. officer@court.demo"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full px-4 py-2.5 rounded-xl bg-slate-950/80 border border-slate-700/80 text-white placeholder-slate-500 text-sm focus:outline-none focus:border-amber-400 focus:ring-1 focus:ring-amber-400 transition-colors"
                />
              </div>

              {/* Password */}
              <div>
                <label
                  htmlFor="court-password"
                  className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1.5"
                >
                  Password
                </label>
                <input
                  id="court-password"
                  type="password"
                  required
                  autoComplete="current-password"
                  disabled={isLoading || isLockedOut}
                  placeholder="••••••••••••"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full px-4 py-2.5 rounded-xl bg-slate-950/80 border border-slate-700/80 text-white placeholder-slate-500 text-sm focus:outline-none focus:border-amber-400 focus:ring-1 focus:ring-amber-400 transition-colors"
                />
              </div>

              {/* Dev Quick-Fill Helpers */}
              <div className="p-2.5 rounded-xl bg-slate-950/60 border border-slate-800 text-[11px] space-y-1">
                <span className="text-slate-400 block font-semibold">Demo Fill:</span>
                <div className="flex gap-2">
                  <button
                    id="btn-fill-officer"
                    type="button"
                    onClick={() => {
                      setEmail("officer@court.demo");
                      setPassword("Demo@1234");
                      setRole("forensic_officer");
                    }}
                    className="text-amber-400 hover:text-amber-300 underline font-mono"
                  >
                    Forensic Officer
                  </button>
                  <span className="text-slate-600">|</span>
                  <button
                    id="btn-fill-judge"
                    type="button"
                    onClick={() => {
                      setEmail("judge@court.demo");
                      setPassword("Demo@1234");
                      setRole("judge");
                    }}
                    className="text-amber-400 hover:text-amber-300 underline font-mono"
                  >
                    Judge
                  </button>
                </div>
              </div>

              <button
                id="court-login-submit"
                type="submit"
                disabled={isLoading || isLockedOut || !email || !password}
                className="w-full py-3 px-4 rounded-xl font-medium text-sm text-white bg-gradient-to-r from-amber-600 to-amber-700 hover:from-amber-500 hover:to-amber-600 shadow-lg shadow-amber-950/50 transition-all flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed pt-3"
              >
                {isLoading ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    <span>Verifying Credentials...</span>
                  </>
                ) : (
                  <>
                    <span>Proceed to 2FA Authentication</span>
                    <ArrowRight className="w-4 h-4" />
                  </>
                )}
              </button>
            </form>
          </>
        ) : (
          <TwoFactorStep
            theme="court"
            email={email}
            onVerify={handleTotpVerify}
            onBack={() => {
              setStep(1);
              setErrorMsg("");
            }}
            isLoading={isLoading}
            errorMessage={errorMsg}
            isLockedOut={isLockedOut}
          />
        )}
      </div>
    </div>
  );
}
