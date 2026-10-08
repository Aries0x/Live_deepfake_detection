"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { ShieldCheck, Video, ArrowLeft, ArrowRight, Loader2, RefreshCw, CheckCircle2, AlertCircle, Lock } from "lucide-react";
import OtpInput from "@/components/auth/OtpInput";
import { getApiBase } from "@/lib/config";
import { setStoredToken } from "@/lib/auth";

export default function CitizenLoginPage() {
  const router = useRouter();

  // Step 1: Identifier input; Step 2: OTP & Consent
  const [step, setStep] = useState<1 | 2>(1);
  const [identifier, setIdentifier] = useState("");
  const [otp, setOtp] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [consent, setConsent] = useState(false);

  // States
  const [isLoading, setIsLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState("");
  const [isLockedOut, setIsLockedOut] = useState(false);
  const [devOtpHint, setDevOtpHint] = useState<string | null>(null);

  // Resend Timer (60s)
  const [resendTimer, setResendTimer] = useState(0);

  useEffect(() => {
    let interval: NodeJS.Timeout;
    if (resendTimer > 0) {
      interval = setInterval(() => {
        setResendTimer((prev) => prev - 1);
      }, 1000);
    }
    return () => clearInterval(interval);
  }, [resendTimer]);

  // Step 1: Request OTP
  const handleRequestOtp = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!identifier.trim()) {
      setErrorMsg("Please enter a valid phone number or email address.");
      return;
    }

    setIsLoading(true);
    setErrorMsg("");

    try {
      const res = await fetch(`${getApiBase()}/auth/citizen/request-otp`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ identifier: identifier.trim() }),
      });

      const data = await res.json();
      if (!res.ok) {
        if (res.status === 429) {
          setIsLockedOut(true);
          setErrorMsg(data.detail || "Too many attempts. Try again in 5 minutes.");
        } else {
          setErrorMsg(data.detail || "Unable to send verification code. Please check your input.");
        }
        return;
      }

      // Success -> move to step 2
      const hint = data.dev_code || data.dev_otp || "123456";
      setDevOtpHint(hint);
      setStep(2);
      setResendTimer(60);
    } catch {
      setErrorMsg("Network error connecting to auth server. Ensure backend is running.");
    } finally {
      setIsLoading(false);
    }
  };

  // Step 2: Verify OTP and Register/Login
  const handleVerifyOtp = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();

    if (otp.length !== 6) {
      setErrorMsg("Please enter the complete 6-digit verification code.");
      return;
    }

    if (!consent) {
      setErrorMsg("You must provide consent for multimodal deepfake analysis to continue.");
      return;
    }

    setIsLoading(true);
    setErrorMsg("");

    try {
      const res = await fetch(`${getApiBase()}/auth/citizen/verify-otp`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({
          identifier: identifier.trim(),
          otp: otp.trim(),
          name: displayName.trim() || undefined,
          consent_given: consent,
        }),
      });

      const data = await res.json();
      if (!res.ok) {
        if (res.status === 429) {
          setIsLockedOut(true);
          setErrorMsg(data.detail || "Too many attempts. Try again in 5 minutes.");
        } else {
          setErrorMsg(data.detail || "Invalid or expired verification code.");
        }
        return;
      }

      if (data.token) {
        setStoredToken(data.token);
      }

      // Successful login -> Redirect to Citizen Dashboard
      router.push("/dashboard/citizen");
    } catch {
      setErrorMsg("Network error verifying code. Please try again.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-[calc(100vh-65px)] flex items-center justify-center p-4 sm:p-6 lg:p-8">
      <div className="w-full max-w-md bg-slate-900/90 border border-cyan-500/20 rounded-2xl p-6 sm:p-8 backdrop-blur-xl shadow-2xl relative overflow-hidden">
        {/* Glow accent */}
        <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-cyan-500 via-teal-400 to-emerald-500" />

        {/* Back Link */}
        <div className="mb-6">
          <Link
            href="/login"
            className="inline-flex items-center gap-1.5 text-xs text-slate-400 hover:text-cyan-400 transition-colors"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            <span>Back to Portal Roles</span>
          </Link>
        </div>

        {/* Icon & Heading */}
        <div className="text-center mb-6">
          <div className="inline-flex p-3 rounded-2xl bg-cyan-500/10 border border-cyan-500/30 text-cyan-400 mb-3 shadow-inner">
            <Video className="w-8 h-8" />
          </div>
          <h1 className="text-2xl font-bold text-white tracking-tight">Citizen Verification</h1>
          <p className="text-xs text-slate-400 mt-1">
            Real-time biometric protection for personal and professional calls
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

        {/* Step 1: Identifier Input */}
        {step === 1 && (
          <form onSubmit={handleRequestOtp} className="space-y-5">
            <div>
              <label
                htmlFor="citizen-identifier"
                className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2"
              >
                Phone Number or Email
              </label>
              <input
                id="citizen-identifier"
                type="text"
                autoComplete="email tel"
                required
                disabled={isLoading || isLockedOut}
                placeholder="e.g. +1 555-0199 or citizen@demo.com"
                value={identifier}
                onChange={(e) => setIdentifier(e.target.value)}
                className="w-full px-4 py-3 rounded-xl bg-slate-950/80 border border-slate-700/80 text-white placeholder-slate-500 text-sm focus:outline-none focus:border-cyan-400 focus:ring-1 focus:ring-cyan-400 transition-colors"
              />
              <p className="text-[11px] text-slate-400 mt-1.5">
                New users will be instantly enrolled. No password required.
              </p>
            </div>

            {/* Quick Fill Dev Helper */}
            <div className="flex items-center justify-between text-[11px] p-2 rounded-lg bg-slate-950/50 border border-slate-800">
              <span className="text-slate-400">Quick Test Account:</span>
              <button
                type="button"
                onClick={() => setIdentifier("citizen@demo.com")}
                className="text-cyan-400 hover:text-cyan-300 font-mono underline decoration-dotted"
              >
                citizen@demo.com
              </button>
            </div>

            <button
              type="submit"
              disabled={isLoading || isLockedOut || !identifier.trim()}
              className="w-full py-3 px-4 rounded-xl font-medium text-sm text-white bg-gradient-to-r from-cyan-600 to-teal-600 hover:from-cyan-500 hover:to-teal-500 shadow-lg shadow-cyan-950/50 transition-all flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isLoading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>Sending Code...</span>
                </>
              ) : (
                <>
                  <span>Send 6-Digit OTP</span>
                  <ArrowRight className="w-4 h-4" />
                </>
              )}
            </button>
          </form>
        )}

        {/* Step 2: OTP Input & Consent */}
        {step === 2 && (
          <form onSubmit={handleVerifyOtp} className="space-y-5">
            <div>
              <div className="flex items-center justify-between mb-2">
                <label className="text-xs font-semibold text-slate-300 uppercase tracking-wider">
                  Verification Code
                </label>
                <button
                  type="button"
                  onClick={() => {
                    setStep(1);
                    setOtp("");
                    setErrorMsg("");
                  }}
                  className="text-[11px] text-cyan-400 hover:underline"
                >
                  Change identifier
                </button>
              </div>

              <OtpInput
                length={6}
                value={otp}
                onChange={setOtp}
                onComplete={(code) => setOtp(code)}
                disabled={isLoading || isLockedOut}
                ariaLabel="6-Digit SMS or Email OTP Code"
              />

              {/* Dev OTP auto-fill banner */}
              {devOtpHint && (
                <div className="mt-2.5 p-2 rounded-lg bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 text-[11px] flex items-center justify-between font-mono">
                  <span>Dev OTP: <strong>{devOtpHint}</strong></span>
                  <button
                    type="button"
                    onClick={() => setOtp(devOtpHint)}
                    className="underline text-emerald-400 hover:text-emerald-300"
                  >
                    Auto-Fill
                  </button>
                </div>
              )}
            </div>

            {/* Display Name Input */}
            <div>
              <label
                htmlFor="citizen-display-name"
                className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2"
              >
                Your Display Name (Optional)
              </label>
              <input
                id="citizen-display-name"
                type="text"
                placeholder="e.g. Alex Rivera"
                value={displayName}
                onChange={(e) => setDisplayName(e.target.value)}
                className="w-full px-4 py-2.5 rounded-xl bg-slate-950/80 border border-slate-700/80 text-white placeholder-slate-500 text-sm focus:outline-none focus:border-cyan-400 focus:ring-1 focus:ring-cyan-400"
              />
            </div>

            {/* Mandatory Biometric Consent Checkbox */}
            <div className="p-3.5 rounded-xl bg-slate-950/80 border border-slate-800 space-y-2">
              <label className="flex items-start gap-3 cursor-pointer">
                <input
                  type="checkbox"
                  required
                  id="citizen-consent"
                  checked={consent}
                  onChange={(e) => setConsent(e.target.checked)}
                  className="mt-1 w-4 h-4 rounded border-slate-700 text-cyan-500 focus:ring-cyan-400 bg-slate-900"
                />
                <span className="text-xs text-slate-300 leading-relaxed">
                  I consent to SecureCall analyzing video and audio in calls I start or join, to detect deepfakes.
                </span>
              </label>
            </div>

            {/* Resend OTP button */}
            <div className="flex items-center justify-between text-xs text-slate-400 pt-1">
              <span>Didn't receive a code?</span>
              <button
                type="button"
                disabled={resendTimer > 0 || isLoading || isLockedOut}
                onClick={() => handleRequestOtp()}
                className="text-cyan-400 hover:text-cyan-300 disabled:text-slate-600 disabled:cursor-not-allowed flex items-center gap-1 font-medium"
              >
                <RefreshCw className={`w-3 h-3 ${isLoading ? "animate-spin" : ""}`} />
                {resendTimer > 0 ? `Resend in ${resendTimer}s` : "Resend OTP"}
              </button>
            </div>

            <button
              type="submit"
              disabled={otp.length !== 6 || !consent || isLoading || isLockedOut}
              className="w-full py-3 px-4 rounded-xl font-medium text-sm text-white bg-gradient-to-r from-cyan-600 to-teal-600 hover:from-cyan-500 hover:to-teal-500 shadow-lg shadow-cyan-950/50 transition-all flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isLoading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>Entering Protected Dashboard...</span>
                </>
              ) : (
                <>
                  <CheckCircle2 className="w-4 h-4" />
                  <span>Verify & Enter Call Suite</span>
                </>
              )}
            </button>
          </form>
        )}
      </div>
    </div>
  );
}
