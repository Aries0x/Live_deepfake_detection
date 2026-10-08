"use client";

import React, { useEffect } from "react";
import { useRouter } from "next/navigation";
import { Loader2, ShieldCheck } from "lucide-react";
import { getMe } from "@/lib/auth";

export default function DashboardRouterPage() {
  const router = useRouter();

  useEffect(() => {
    getMe().then((user) => {
      if (!user) {
        router.replace("/login");
        return;
      }

      switch (user.role) {
        case "citizen":
          router.replace("/dashboard/citizen");
          break;
        case "forensic_officer":
          router.replace("/dashboard/forensic");
          break;
        case "judge":
          router.replace("/dashboard/judge");
          break;
        case "admin":
          router.replace("/dashboard/admin");
          break;
        default:
          router.replace("/login");
          break;
      }
    });
  }, [router]);

  return (
    <div className="min-h-[calc(100vh-65px)] flex flex-col items-center justify-center space-y-4">
      <div className="p-4 rounded-2xl bg-slate-900 border border-slate-800 text-cyan-400 shadow-xl">
        <ShieldCheck className="w-10 h-10 animate-pulse text-cyan-400" />
      </div>
      <div className="flex items-center gap-2 text-slate-300 text-sm font-medium">
        <Loader2 className="w-4 h-4 animate-spin text-cyan-400" />
        <span>Routing to authenticated role dashboard...</span>
      </div>
    </div>
  );
}
