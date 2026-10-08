"use client";

import React from "react";
import Link from "next/link";
import { ArrowRight, Shield, Scale, LucideIcon } from "lucide-react";

interface RoleCardProps {
  title: string;
  badge: string;
  description: string;
  features: string[];
  href: string;
  theme: "citizen" | "court" | "admin";
  icon: LucideIcon;
  ctaText: string;
}

export default function RoleCard({
  title,
  badge,
  description,
  features,
  href,
  theme,
  icon: Icon,
  ctaText,
}: RoleCardProps) {
  const themeStyles = {
    citizen: {
      card: "border-cyan-500/20 bg-gradient-to-b from-slate-900/90 to-cyan-950/20 hover:border-cyan-400/50 hover:shadow-[0_0_30px_rgba(6,182,212,0.15)]",
      badge: "bg-cyan-500/10 text-cyan-400 border-cyan-500/30",
      icon: "bg-cyan-500/10 text-cyan-400 border-cyan-500/20",
      button: "bg-gradient-to-r from-cyan-600 to-teal-600 hover:from-cyan-500 hover:to-teal-500 text-white shadow-lg shadow-cyan-950/50",
      dot: "bg-cyan-400",
    },
    court: {
      card: "border-amber-500/20 bg-gradient-to-b from-slate-900/90 to-amber-950/20 hover:border-amber-400/50 hover:shadow-[0_0_30px_rgba(245,158,11,0.15)]",
      badge: "bg-amber-500/10 text-amber-400 border-amber-500/30",
      icon: "bg-amber-500/10 text-amber-400 border-amber-500/20",
      button: "bg-gradient-to-r from-amber-600 to-amber-700 hover:from-amber-500 hover:to-amber-600 text-white shadow-lg shadow-amber-950/50",
      dot: "bg-amber-400",
    },
    admin: {
      card: "border-rose-500/20 bg-gradient-to-b from-slate-900/90 to-rose-950/20 hover:border-rose-400/50 hover:shadow-[0_0_30px_rgba(244,63,94,0.15)]",
      badge: "bg-rose-500/10 text-rose-400 border-rose-500/30",
      icon: "bg-rose-500/10 text-rose-400 border-rose-500/20",
      button: "bg-gradient-to-r from-rose-600 to-red-700 hover:from-rose-500 hover:to-red-600 text-white shadow-lg shadow-rose-950/50",
      dot: "bg-rose-400",
    },
  }[theme];

  return (
    <Link
      href={href}
      className={`group relative flex flex-col justify-between rounded-2xl border p-8 transition-all duration-300 backdrop-blur-xl ${themeStyles.card}`}
    >
      <div>
        <div className="flex items-center justify-between mb-6">
          <div className={`p-3 rounded-xl border ${themeStyles.icon}`}>
            <Icon className="w-7 h-7" />
          </div>
          <span
            className={`text-xs font-semibold uppercase tracking-wider px-3 py-1 rounded-full border ${themeStyles.badge}`}
          >
            {badge}
          </span>
        </div>

        <h3 className="text-2xl font-bold text-white group-hover:text-cyan-100 transition-colors mb-3">
          {title}
        </h3>
        <p className="text-sm text-slate-300/90 leading-relaxed mb-6">
          {description}
        </p>

        <ul className="space-y-2.5 mb-8">
          {features.map((feature, i) => (
            <li key={i} className="flex items-center text-xs text-slate-300">
              <span className={`w-1.5 h-1.5 rounded-full mr-2.5 ${themeStyles.dot}`} />
              {feature}
            </li>
          ))}
        </ul>
      </div>

      <div className="pt-4 border-t border-slate-800/80">
        <div
          className={`w-full py-3 px-4 rounded-xl font-medium text-sm flex items-center justify-center gap-2 transition-transform duration-200 group-hover:translate-x-1 ${themeStyles.button}`}
        >
          <span>{ctaText}</span>
          <ArrowRight className="w-4 h-4 transition-transform group-hover:translate-x-1" />
        </div>
      </div>
    </Link>
  );
}
