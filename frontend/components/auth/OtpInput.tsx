"use client";

import React, { useRef, useState, useEffect } from "react";

interface OtpInputProps {
  length?: number;
  value: string;
  onChange: (otp: string) => void;
  onComplete?: (otp: string) => void;
  disabled?: boolean;
  accentColor?: "teal" | "amber" | "red";
  ariaLabel?: string;
}

export default function OtpInput({
  length = 6,
  value,
  onChange,
  onComplete,
  disabled = false,
  accentColor = "teal",
  ariaLabel = "Verification code digit",
}: OtpInputProps) {
  const inputsRef = useRef<(HTMLInputElement | null)[]>([]);
  const [digits, setDigits] = useState<string[]>(Array(length).fill(""));

  useEffect(() => {
    const arr = value.split("").slice(0, length);
    while (arr.length < length) arr.push("");
    setDigits(arr);
  }, [value, length]);

  const handleChange = (index: number, e: React.ChangeEvent<HTMLInputElement>) => {
    const val = e.target.value.replace(/\D/g, "");
    if (!val) {
      const next = [...digits];
      next[index] = "";
      setDigits(next);
      const newOtp = next.join("");
      onChange(newOtp);
      return;
    }

    const next = [...digits];
    // If user typed a single digit
    next[index] = val.slice(-1);
    setDigits(next);
    const newOtp = next.join("");
    onChange(newOtp);

    if (newOtp.length === length && onComplete) {
      onComplete(newOtp);
    }

    // Auto-advance
    if (index < length - 1) {
      inputsRef.current[index + 1]?.focus();
    }
  };

  const handleKeyDown = (index: number, e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Backspace" && !digits[index] && index > 0) {
      inputsRef.current[index - 1]?.focus();
    } else if (e.key === "ArrowLeft" && index > 0) {
      inputsRef.current[index - 1]?.focus();
    } else if (e.key === "ArrowRight" && index < length - 1) {
      inputsRef.current[index + 1]?.focus();
    }
  };

  const handlePaste = (e: React.ClipboardEvent<HTMLInputElement>) => {
    e.preventDefault();
    const pasted = e.clipboardData.getData("text").replace(/\D/g, "").slice(0, length);
    if (!pasted) return;

    const next = [...digits];
    for (let i = 0; i < pasted.length; i++) {
      next[i] = pasted[i];
    }
    setDigits(next);
    const newOtp = next.join("");
    onChange(newOtp);

    if (newOtp.length === length && onComplete) {
      onComplete(newOtp);
    }

    const nextFocus = Math.min(pasted.length, length - 1);
    inputsRef.current[nextFocus]?.focus();
  };

  const borderStyles = {
    teal: "focus:border-cyan-400 focus:ring-cyan-500/20",
    amber: "focus:border-amber-400 focus:ring-amber-500/20",
    red: "focus:border-rose-500 focus:ring-rose-500/20",
  }[accentColor];

  return (
    <div className="flex items-center justify-center gap-2 sm:gap-3">
      {digits.map((digit, idx) => (
        <input
          key={idx}
          ref={(el) => {
            inputsRef.current[idx] = el;
          }}
          type="text"
          inputMode="numeric"
          pattern="[0-9]*"
          maxLength={1}
          value={digit}
          disabled={disabled}
          onChange={(e) => handleChange(idx, e)}
          onKeyDown={(e) => handleKeyDown(idx, e)}
          onPaste={handlePaste}
          aria-label={`Digit ${idx + 1}`}
          className={`w-11 h-14 sm:w-13 sm:h-16 text-center text-xl sm:text-2xl font-bold font-mono rounded-xl bg-slate-900/90 border border-slate-700/80 text-white focus:outline-none focus:ring-4 transition-all duration-150 ${borderStyles} ${
            disabled ? "opacity-50 cursor-not-allowed" : "cursor-text"
          } ${digit ? "border-slate-500 bg-slate-800/80 shadow-inner" : ""}`}
        />
      ))}
    </div>
  );
}
