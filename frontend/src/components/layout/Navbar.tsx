import React, { useState } from "react";
import { Link, useLocation } from "react-router-dom";
import { Waves, Cpu, Menu, Sparkles } from "lucide-react";
import { useQuery } from "@tanstack/react-query";
import { systemApi } from "../../api/client";

export const Navbar: React.FC = () => {
  const location = useLocation();
  const [isMobileMenuOpen, setMobileMenuOpen] = useState(false);
  const { data: health } = useQuery({
    queryKey: ["system-health"],
    queryFn: systemApi.getHealth,
    refetchInterval: 10000,
    retry: 1,
  });

  const isHealthy = health?.status === "ok";

  // Dynamic context derivation based on path
  let pageTitle = "Command Center";
  let pageSubtitle = "Marine intelligence, in context";

  if (location.pathname.startsWith("/surveys/") && location.pathname !== "/surveys") {
    pageTitle = "Evidence Room";
    pageSubtitle = "Acoustic evidence & geographic context";
  } else if (location.pathname === "/surveys") {
    pageTitle = "Expeditions";
    pageSubtitle = "Survey records & field history";
  } else if (location.pathname === "/upload") {
    pageTitle = "Start an Expedition";
    pageSubtitle = "Bring source data into the evidence chain";
  } else if (location.pathname === "/models") {
    pageTitle = "Intelligence Registry";
    pageSubtitle = "Model release & readiness records";
  } else if (location.pathname === "/dataset") {
    pageTitle = "Dataset Explorer";
    pageSubtitle = "Marine Debris FLS Benchmark (3.0 MHz ARIS 3000)";
  }

  return (
    <header className="site-header h-14 border-b border-border-subtle bg-bg-surface px-4 md:px-6 flex items-center justify-between sticky top-0 z-30 shadow-subtle">
      {/* Brand & Page Context */}
      <div className="flex items-center gap-3 md:gap-6">
        <Link to="/" className="brand-mark flex items-center gap-2.5">
          <div className="brand-mark__symbol w-8 h-8 rounded-full bg-accent text-white flex items-center justify-center shadow-sm">
            <Waves className="w-4 h-4" strokeWidth={1.8} />
          </div>
          <div>
            <div className="font-bold text-text-primary text-sm tracking-tight flex items-center gap-1.5 leading-none">
              <span>MarineDebris</span><span className="brand-mark__sub">FIELD SYSTEMS</span>
            </div>
            <span className="text-[10px] font-mono text-text-muted">Acoustic intelligence</span>
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
        <div className="hidden xl:flex items-center gap-1.5 px-2.5 py-1 bg-bg-elevated border border-border-subtle rounded-full text-xs font-mono text-text-secondary">
          <Cpu className="w-3.5 h-3.5 text-accent" />
          <span>Device:</span>
          <span className="font-semibold text-text-primary">{health?.device || "CPU"}</span>
        </div>

        {/* System Health status */}
        <div className="flex items-center gap-2 px-3 py-1 bg-bg-elevated border border-border-subtle rounded-full text-xs font-medium text-text-secondary">
          <span
            className={`w-2 h-2 rounded-full ${
              isHealthy ? "bg-emerald-500 shadow-sm" : "bg-amber-500"
            }`}
          />
          <span className="text-text-primary font-mono text-[11px]">
            {health ? (isHealthy ? "SYSTEM NORMAL" : "DEGRADED") : "CONNECTING..."}
          </span>
        </div>

        <span className="hidden lg:inline-flex items-center gap-1 px-2.5 py-1 rounded-full bg-[#F8EAC3] text-[#755419] border border-[#E9D49A] text-[11px] font-mono font-semibold">
          <Sparkles className="w-3.5 h-3.5" />
          FIELD MODE
        </span>
        <button
          type="button"
          className="mobile-menu-trigger lg:hidden"
          aria-label="Open navigation"
          aria-expanded={isMobileMenuOpen}
          aria-controls="mobile-navigation"
          onClick={() => setMobileMenuOpen((open) => !open)}
        >
          <Menu className="w-5 h-5" aria-hidden="true" />
        </button>
      </div>
      {isMobileMenuOpen && (
        <nav id="mobile-navigation" className="mobile-navigation" aria-label="Mobile navigation">
          <Link to="/" onClick={() => setMobileMenuOpen(false)}>Command center</Link>
          <Link to="/surveys" onClick={() => setMobileMenuOpen(false)}>Expeditions</Link>
          <Link to="/upload" onClick={() => setMobileMenuOpen(false)}>Start an expedition</Link>
          <Link to="/enhancement" onClick={() => setMobileMenuOpen(false)}>Signal lab</Link>
          <Link to="/models" onClick={() => setMobileMenuOpen(false)}>Intelligence registry</Link>
          <Link to="/dataset" onClick={() => setMobileMenuOpen(false)}>Dataset provenance</Link>
        </nav>
      )}
    </header>
  );
};

export default Navbar;
