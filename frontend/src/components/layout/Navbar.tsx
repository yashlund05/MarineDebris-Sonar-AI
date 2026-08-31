import React from "react";
import { Waves, Cpu } from "lucide-react";
import { useQuery } from "@tanstack/react-query";
import { systemApi } from "../../api/client";

export const Navbar: React.FC = () => {
  const { data: health } = useQuery({
    queryKey: ["system-health"],
    queryFn: systemApi.getHealth,
    refetchInterval: 10000,
    retry: 1,
  });

  const isHealthy = health?.status === "ok";

  return (
    <header className="h-14 border-b border-border-subtle bg-bg-surface px-4 flex items-center justify-between sticky top-0 z-30">
      <div className="flex items-center space-x-3">
        <div className="w-8 h-8 rounded-md bg-accent/20 border border-accent/40 flex items-center justify-center text-accent">
          <Waves className="w-5 h-5" />
        </div>
        <div className="flex items-center space-x-2">
          <span className="font-bold text-text-primary text-base tracking-tight">
            MarineDebris-Sonar-AI
          </span>
          <span className="text-xs px-2 py-0.5 rounded bg-bg-elevated text-text-secondary border border-border-subtle font-mono">
            PS26057
          </span>
          <span className="text-xs px-2 py-0.5 rounded bg-blue-950/60 text-accent border border-accent/30 font-mono">
            SPEC v1.0.0 FROZEN
          </span>
        </div>
      </div>

      <div className="flex items-center space-x-4">
        <div className="flex items-center space-x-2 text-xs">
          <span className="text-text-secondary flex items-center gap-1">
            <Cpu className="w-3.5 h-3.5" />
            Device: <span className="font-mono text-text-primary">{health?.device || "detecting..."}</span>
          </span>
        </div>
        <div className="flex items-center space-x-2 text-xs">
          <span
            className={`w-2 h-2 rounded-full ${
              isHealthy ? "bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.6)]" : "bg-amber-500"
            }`}
          />
          <span className="text-text-secondary font-medium">
            API: {health ? (isHealthy ? "Online" : "Degraded") : "Connecting..."}
          </span>
        </div>
      </div>
    </header>
  );
};
