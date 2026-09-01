import React from "react";
import { Link, useLocation } from "react-router-dom";
import { Waves, Cpu, ShieldCheck } from "lucide-react";
import { useQuery } from "@tanstack/react-query";
import { systemApi } from "../../api/client";

export const Navbar: React.FC = () => {
  const location = useLocation();
  const { data: health } = useQuery({
    queryKey: ["system-health"],
    queryFn: systemApi.getHealth,
    refetchInterval: 10000,
    retry: 1,
  });

  const isHealthy = health?.status === "ok";

  // Dynamic context derivation based on path
  let pageTitle = "Overview";
  let pageSubtitle = "Operational Acoustic Dashboard";

  if (location.pathname.startsWith("/surveys/") && location.pathname !== "/surveys") {
    pageTitle = "Sonar Analysis";
    pageSubtitle = "High-Resolution Acoustic Imaging Workstation";
  } else if (location.pathname === "/surveys") {
    pageTitle = "Surveys Archive";
    pageSubtitle = "Historical Acoustic Sessions & Records";
  } else if (location.pathname === "/upload") {
    pageTitle = "Survey Ingestion";
    pageSubtitle = "Upload Sonar Raw Imagery & Metadata";
  } else if (location.pathname === "/models") {
    pageTitle = "Model Center";
    pageSubtitle = "Acoustic AI Models & Readiness Matrix";
  } else if (location.pathname === "/dataset") {
    pageTitle = "Dataset Explorer";
    pageSubtitle = "Marine Debris FLS Benchmark (3.0 MHz ARIS 3000)";
  }

  return (
    <header className="h-14 border-b border-border-subtle bg-bg-surface px-6 flex items-center justify-between sticky top-0 z-30 shadow-subtle">
      {/* Brand & Page Context */}
      <div className="flex items-center gap-6">
        <Link to="/" className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-lg bg-accent text-white flex items-center justify-center shadow-sm">
            <Waves className="w-4 h-4" />
          </div>
          <div>
            <div className="font-bold text-text-primary text-sm tracking-tight flex items-center gap-1.5 leading-none">
              <span>MarineDebris</span>
              <span className="text-[10px] px-1.5 py-0.5 rounded bg-sky-100 text-sky-800 font-mono font-semibold">
                SONAR AI
              </span>
            </div>
            <span className="text-[10px] font-mono text-text-muted">SIH 2026 • PS26057</span>
          </div>
        </Link>

        <div className="h-6 w-px bg-border-subtle hidden sm:block" />

        <div className="hidden sm:block">
          <div className="text-xs font-bold text-text-primary leading-tight">{pageTitle}</div>
          <div className="text-[11px] text-text-muted leading-none mt-0.5">{pageSubtitle}</div>
        </div>
      </div>

      {/* Right Telemetry & Status Badges */}
      <div className="flex items-center gap-3">
        {/* Device indicator */}
        <div className="hidden md:flex items-center gap-1.5 px-2.5 py-1 bg-bg-elevated border border-border-subtle rounded-lg text-xs font-mono text-text-secondary">
          <Cpu className="w-3.5 h-3.5 text-accent" />
          <span>Device:</span>
          <span className="font-semibold text-text-primary">{health?.device || "CPU"}</span>
        </div>

        {/* System Health status */}
        <div className="flex items-center gap-2 px-3 py-1 bg-bg-elevated border border-border-subtle rounded-lg text-xs font-medium text-text-secondary">
          <span
            className={`w-2 h-2 rounded-full ${
              isHealthy ? "bg-emerald-500 shadow-sm" : "bg-amber-500"
            }`}
          />
          <span className="text-text-primary font-mono text-[11px]">
            {health ? (isHealthy ? "SYSTEM NORMAL" : "DEGRADED") : "CONNECTING..."}
          </span>
        </div>

        {/* Spec Badge */}
        <span className="hidden lg:inline-flex items-center gap-1 px-2.5 py-1 rounded-lg bg-slate-100 text-slate-700 border border-slate-200 text-[11px] font-mono font-semibold">
          <ShieldCheck className="w-3.5 h-3.5 text-emerald-600" />
          SPEC v1.0 FROZEN
        </span>
      </div>
    </header>
  );
};

export default Navbar;
