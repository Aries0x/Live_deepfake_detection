"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  ShieldCheck,
  Video,
  LayoutDashboard,
  Layers,
  Cpu,
  LogOut,
  LogIn,
  Scale,
  Activity,
  User as UserIcon,
} from "lucide-react";
import { getApiBase } from "@/lib/config";
import { getMe, logout, can, UserSession } from "@/lib/auth";

export default function Navbar() {
  const pathname = usePathname();
  const [backendStatus, setBackendStatus] = useState<{ online: boolean; gpu: string } | null>(null);
  const [user, setUser] = useState<UserSession | null>(null);

  useEffect(() => {
    getMe().then((u) => setUser(u));
  }, [pathname]);

  useEffect(() => {
    const checkHealth = async () => {
      try {
        const res = await fetch(`${getApiBase()}/api/v1/health`);
        if (res.ok) {
          const data = await res.json();
          setBackendStatus({
            online: true,
            gpu: data.gpu?.name ? data.gpu.name.replace("NVIDIA GeForce ", "") : "GPU Ready",
          });
        } else {
          setBackendStatus({ online: false, gpu: "Offline" });
        }
      } catch {
        setBackendStatus({ online: false, gpu: "Connecting..." });
      }
    };
    checkHealth();
    const interval = setInterval(checkHealth, 8000);
    return () => clearInterval(interval);
  }, []);

  // Compute dynamic navigation items based on user login state and role permissions
  const getNavItems = () => {
    if (!user) {
      // Unauthenticated: only public information
      return [
        { name: "Model Registry", href: "/models", icon: Cpu },
      ];
    }

    const items: Array<{ name: string; href: string; icon: any }> = [];

    // Live Call (for all authenticated roles)
    if (can(user, "live_call.join")) {
      items.push({
        name: user.role === "judge" ? "Hearing Call" : "Live Call",
        href: "/call",
        icon: user.role === "judge" ? Scale : Video,
      });
    }

    // Role-specific Dashboard
    const dashboardHref = `/dashboard/${user.role === "forensic_officer" ? "forensic" : user.role}`;
    items.push({
      name: "Dashboard",
      href: dashboardHref,
      icon: LayoutDashboard,
    });

    // Bulk Verification (ONLY for Forensic Officer or Admin - HIDDEN from Citizen and Judge)
    if (can(user, "bulk.upload_videos") || can(user, "bulk.create_case")) {
      items.push({
        name: "Bulk Verification",
        href: "/bulk",
        icon: Layers,
      });
    }

    // Model Registry
    items.push({
      name: "Model Registry",
      href: "/models",
      icon: Cpu,
    });

    return items;
  };

  const navItems = getNavItems();

  const roleConfig = {
    citizen: {
      label: "CITIZEN",
      badge: "bg-cyan-500/15 text-cyan-300 border-cyan-500/30",
    },
    forensic_officer: {
      label: "FORENSIC",
      badge: "bg-amber-500/15 text-amber-300 border-amber-500/30",
    },
    judge: {
      label: "JUDGE",
      badge: "bg-amber-500/15 text-amber-300 border-amber-500/30",
    },
    admin: {
      label: "ADMIN",
      badge: "bg-rose-500/15 text-rose-300 border-rose-500/30",
    },
  }[user?.role || "citizen"];

  return (
    <nav className="w-full border-b border-slate-800/80 bg-[#0b0f19]/95 backdrop-blur-xl sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 h-16 flex items-center justify-between gap-4">
        {/* Left: Brand Identity */}
        <Link href="/" className="flex items-center gap-3 shrink-0 group">
          <div className="w-9 h-9 rounded-xl bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center text-emerald-400 group-hover:scale-105 group-hover:border-emerald-500/50 transition-all shadow-inner">
            <ShieldCheck className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2 leading-none">
              <span className="font-extrabold text-base text-white tracking-wider">SECURECALL</span>
              <span className="text-[9px] uppercase font-mono font-bold px-1.5 py-0.5 rounded bg-blue-500/20 text-blue-400 border border-blue-500/30">
                FORENSICS
              </span>
            </div>
            <p className="text-[11px] text-slate-400 mt-1 hidden sm:block leading-none">
              Real-Time Multimodal Media Integrity
            </p>
          </div>
        </Link>

        {/* Center: Structured Navigation Pill Group */}
        <div className="hidden md:flex items-center">
          <div className="flex items-center gap-1 bg-slate-950/70 p-1 rounded-2xl border border-slate-800/80 shadow-inner">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = pathname === item.href || (item.href !== "/" && pathname.startsWith(item.href));
              return (
                <Link
                  key={item.name}
                  href={item.href}
                  className={`h-8 px-3.5 rounded-xl text-xs font-medium flex items-center gap-2 transition-all ${
                    isActive
                      ? "bg-slate-800 text-white font-semibold shadow-sm border border-slate-700/80"
                      : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/40 border border-transparent"
                  }`}
                >
                  <Icon className={`w-3.5 h-3.5 ${isActive ? "text-cyan-400" : "text-slate-500"}`} />
                  <span>{item.name}</span>
                </Link>
              );
            })}
          </div>
        </div>

        {/* Right: Telemetry & Authenticated User Capsule */}
        <div className="flex items-center gap-2.5 shrink-0">
          {/* Hardware & Backend Status Pill */}
          <div className="h-9 px-3 rounded-xl bg-slate-950/70 border border-slate-800/80 flex items-center gap-2 text-xs font-mono shadow-inner">
            <span
              className={`w-2 h-2 rounded-full shrink-0 ${
                backendStatus?.online ? "bg-emerald-400 animate-pulse" : "bg-amber-400"
              }`}
            />
            <span className="text-slate-400 text-[11px] hidden lg:inline max-w-[150px] truncate">
              {backendStatus?.online ? backendStatus.gpu : "Connecting..."}
            </span>
          </div>

          {/* User Profile Pill or Sign In Button */}
          {user ? (
            <div className="h-9 pl-2 pr-1.5 rounded-xl bg-slate-950/80 border border-slate-800/80 flex items-center gap-2 shadow-sm">
              {/* Role Badge */}
              <span
                className={`text-[9px] font-mono font-bold uppercase px-2 py-0.5 rounded-lg border ${roleConfig.badge}`}
              >
                {roleConfig.label}
              </span>

              {/* User Name */}
              <span className="text-xs text-slate-200 font-medium max-w-[110px] truncate hidden sm:inline-block">
                {user.name}
              </span>

              {/* Vertical Separator */}
              <span className="h-4 w-px bg-slate-800 hidden sm:block" />

              {/* Sign Out Button */}
              <button
                onClick={() => logout()}
                title="Sign Out"
                className="w-6 h-6 rounded-lg flex items-center justify-center text-slate-400 hover:text-rose-400 hover:bg-rose-500/10 transition-colors"
              >
                <LogOut className="w-3.5 h-3.5" />
              </button>
            </div>
          ) : (
            <Link
              href="/login"
              className="h-9 px-3.5 rounded-xl bg-cyan-600 hover:bg-cyan-500 text-white text-xs font-semibold shadow-lg shadow-cyan-950/40 flex items-center gap-1.5 transition-all"
            >
              <LogIn className="w-3.5 h-3.5" />
              <span>Portal Sign In</span>
            </Link>
          )}
        </div>
      </div>
    </nav>
  );
}
