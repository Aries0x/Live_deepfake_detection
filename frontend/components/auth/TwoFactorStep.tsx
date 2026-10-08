"use client";

import React, { useState } from "react";
import { ShieldAlert, KeyRound, Loader2, ArrowLeft, Lock, Info } from "lucide-react";
import OtpInput from "@/components/auth/OtpInput";

interface TwoFactorStepProps {
  theme: "court" | "admin";
  email: string;
  onVerify: (code: string) => Promise<void>;
  onBack: () => void;
  isLoading: boolean;
  errorMessage?: string;
  isLockedOut?: boolean;
}

export default function TwoFactorStep({
  theme,
  email,
  onVerify,
  onBack,
  isLoading,
  errorMessage,
  isLockedOut = false,
}: TwoFactorStepProps) {
  const [totpCode, setTotpCode] = useState("");

  const themeConfig = {
    court: {
      accent: "text-amber-400",
      border: "border-amber-500/30",
      button: "bg-amber-600 hover:bg-amber-500 text-white shadow-amber-950/40",
      bannerBorder: "border-amber-500/20 bg-amber-500/10 text-amber-300",
      inputFocus: "focus:border-amber-400",
      badge: "bg-amber-500/10 text-amber-400 border-amber-500/30",
    },
    admin: {
      accent: "text-rose-400",
      border: "border-rose-500/30",
      button: "bg-rose-600 hover:bg-rose-500 text-white shadow-rose-950/40",
      bannerBorder: "border-rose-500/20 bg-rose-500/10 text-rose-300",
      inputFocus: "focus:border-rose-400",
      badge: "bg-rose-500/10 text-rose-400 border-rose-500/30",
    },
  }[theme];

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (totpCode.length === 6 && !isLoading && !isLockedOut) {
      onVerify(totpCode);
    }
  };

  return (
    <div className="w-full max-w-md mx-auto">
      {/* Header */}
      <div className="text-center mb-6">
        <div className="inline-flex p-3 rounded-2xl bg-slate-900 border border-slate-800 text-slate-200 mb-3 shadow-inner">
          <KeyRound className={`w-8 h-8 ${themeConfig.accent}`} />
        </div>
        <h2 className="text-2xl font-bold text-white tracking-tight">Two-Factor Authentication</h2>
        <p className="text-xs text-slate-400 mt-1">
          Enter the 6-digit TOTP code from your authenticator app for <span className="font-mono text-slate-300">{email}</span>
        </p>
      </div>

      {/* Mandatory Tamper-Evident Warning Banner */}
      <div className={`p-3.5 rounded-xl border flex items-start gap-3 mb-6 text-xs ${themeConfig.bannerBorder}`}>
        <ShieldAlert className="w-4 h-4 mt-0.5 shrink-0" />
        <div>
          <p className="font-semibold tracking-wide uppercase text-[11px]">Chain of Custody Notice</p>
          <p className="text-slate-300/90 mt-0.5 leading-relaxed">
            All authentication attempts, sessions, and forensic verifications are cryptographically anchored to a tamper-evident SHA-256 audit chain.
          </p>
        </div>
      </div>

      {/* Lockout Warning */}
      {isLockedOut && (
        <div className="p-4 rounded-xl border border-rose-500/40 bg-rose-500/10 text-rose-200 mb-6 text-xs flex items-center gap-3">
          <Lock className="w-5 h-5 text-rose-400 shrink-0" />
          <p className="font-medium">
            Too many attempts. Account locked for 5 minutes. Please wait before retrying.
          </p>
        </div>
      )}

      {/* Error Message */}
      {errorMessage && !isLockedOut && (
        <div
          role="alert"
          aria-live="assertive"
          className="p-3 rounded-lg border border-red-500/30 bg-red-950/40 text-red-300 text-xs mb-5 flex items-center gap-2"
        >
          <Info className="w-4 h-4 text-red-400 shrink-0" />
          <span>{errorMessage}</span>
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-6">
        <div>
          <label className="block text-xs font-medium text-slate-300 mb-3 text-center">
            6-Digit Authenticator Code
          </label>
          <OtpInput
            length={6}
            value={totpCode}
            onChange={setTotpCode}
            onComplete={(code) => {
              if (!isLoading && !isLockedOut) {
                onVerify(code);
              }
            }}
            disabled={isLoading || isLockedOut}
            ariaLabel="TOTP Two-Factor Authentication Code"
          />
        </div>

        {/* Dev hint banner */}
        <div className="p-2.5 rounded-lg bg-slate-900/60 border border-slate-800 text-[11px] text-slate-400 flex items-center justify-between font-mono">
          <span>Dev Master Code:</span>
          <button
            type="button"
            onClick={() => {
              setTotpCode("123456");
              if (!isLoading && !isLockedOut) {
                onVerify("123456");
              }
            }}
            className="text-cyan-400 hover:text-cyan-300 font-semibold underline decoration-dotted"
          >
            Fill "123456"
          </button>
        </div>

        <button
          type="submit"
          disabled={totpCode.length !== 6 || isLoading || isLockedOut}
          className={`w-full py-3 px-4 rounded-xl font-medium text-sm transition-all duration-200 flex items-center justify-center gap-2 shadow-lg disabled:opacity-50 disabled:cursor-not-allowed ${themeConfig.button}`}
        >
          {isLoading ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" />
              <span>Verifying Token...</span>
            </>
          ) : (
            <span>Verify & Authenticate</span>
          )}
        </button>

        <button
          type="button"
          onClick={onBack}
          disabled={isLoading}
          className="w-full py-2.5 text-xs text-slate-400 hover:text-slate-200 transition-colors flex items-center justify-center gap-1.5"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          <span>Back to credentials</span>
        </button>
      </form>
    </div>
  );
}
