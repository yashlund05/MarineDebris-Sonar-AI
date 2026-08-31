import React from "react";
import { useQuery } from "@tanstack/react-query";
import { systemApi } from "../api/client";
import { LoadingState } from "../components/ui/LoadingState";
import { ErrorState } from "../components/ui/ErrorState";
import { Database, Server, Cpu, CheckCircle2, ShieldCheck, Layers } from "lucide-react";

export const DashboardPlaceholderPage: React.FC = () => {
  const { data: health, isLoading, isError, refetch } = useQuery({
    queryKey: ["system-health"],
    queryFn: systemApi.getHealth,
    refetchInterval: 15000,
  });

  return (
    <div className="space-y-6">
      <div className="border-b border-border-subtle pb-4">
        <h1 className="text-2xl font-bold text-text-primary tracking-tight">
          System Overview & Engineering Foundation
        </h1>
        <p className="text-sm text-text-secondary mt-1">
          SIH 2026 PS26057 — AI-Powered Automated Underwater Marine Debris and Anomaly Detection System
        </p>
      </div>

      {isLoading && <LoadingState message="Checking backend, database, and cache connections..." />}
      {isError && (
        <ErrorState
          title="Backend Service Unreachable"
          message="Could not connect to FastAPI backend at /api/v1. Ensure backend container or server is running."
          onRetry={() => refetch()}
        />
      )}

      {health && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-bg-surface border border-border-subtle p-4 rounded-lg space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-xs text-text-secondary uppercase font-semibold">Database (PostgreSQL)</span>
              <Database className="w-4 h-4 text-accent" />
            </div>
            <div className="flex items-center space-x-2">
              <span
                className={`w-2.5 h-2.5 rounded-full ${
                  health.database === "connected" ? "bg-emerald-500" : "bg-amber-500"
                }`}
              />
              <span className="font-mono text-sm font-semibold capitalize text-text-primary">
                {health.database}
              </span>
            </div>
          </div>

          <div className="bg-bg-surface border border-border-subtle p-4 rounded-lg space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-xs text-text-secondary uppercase font-semibold">Cache & Broker (Redis)</span>
              <Server className="w-4 h-4 text-accent" />
            </div>
            <div className="flex items-center space-x-2">
              <span
                className={`w-2.5 h-2.5 rounded-full ${
                  health.redis === "connected" ? "bg-emerald-500" : "bg-amber-500"
                }`}
              />
              <span className="font-mono text-sm font-semibold capitalize text-text-primary">
                {health.redis}
              </span>
            </div>
          </div>

          <div className="bg-bg-surface border border-border-subtle p-4 rounded-lg space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-xs text-text-secondary uppercase font-semibold">Inference Worker</span>
              <Cpu className="w-4 h-4 text-accent" />
            </div>
            <div className="flex items-center space-x-2">
              <span
                className={`w-2.5 h-2.5 rounded-full ${
                  health.worker === "running" ? "bg-emerald-500" : "bg-blue-500"
                }`}
              />
              <span className="font-mono text-sm font-semibold capitalize text-text-primary">
                {health.worker} ({health.device})
              </span>
            </div>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-bg-surface border border-border-subtle rounded-lg p-5 space-y-4">
          <div className="flex items-center space-x-2 text-text-primary font-semibold">
            <ShieldCheck className="w-5 h-5 text-emerald-400" />
            <h2>Phase 0 Status: Engineering Foundation Ready</h2>
          </div>
          <ul className="space-y-2 text-sm text-text-secondary">
            <li className="flex items-start space-x-2">
              <CheckCircle2 className="w-4 h-4 text-emerald-500 mt-0.5 shrink-0" />
              <span>FastAPI backend application factory and structured error handling initialized.</span>
            </li>
            <li className="flex items-start space-x-2">
              <CheckCircle2 className="w-4 h-4 text-emerald-500 mt-0.5 shrink-0" />
              <span>SQLAlchemy 2.0 async models and Alembic migrations matching DB_SCHEMA.md.</span>
            </li>
            <li className="flex items-start space-x-2">
              <CheckCircle2 className="w-4 h-4 text-emerald-500 mt-0.5 shrink-0" />
              <span>Celery worker task queue and Redis connection configured.</span>
            </li>
            <li className="flex items-start space-x-2">
              <CheckCircle2 className="w-4 h-4 text-emerald-500 mt-0.5 shrink-0" />
              <span>React 18 + Vite + TypeScript frontend shell configured with UI_UX_SPEC tokens.</span>
            </li>
          </ul>
        </div>

        <div className="bg-bg-surface border border-border-subtle rounded-lg p-5 space-y-4">
          <div className="flex items-center space-x-2 text-text-primary font-semibold">
            <Layers className="w-5 h-5 text-accent" />
            <h2>Implementation Roadmap</h2>
          </div>
          <div className="space-y-3 text-xs">
            <div className="p-2.5 rounded bg-bg-elevated border border-accent/30 flex justify-between items-center">
              <span className="font-semibold text-text-primary">Phase 0: Engineering Foundation</span>
              <span className="text-emerald-400 font-mono font-medium">COMPLETE</span>
            </div>
            <div className="p-2.5 rounded bg-bg-elevated border border-border-subtle flex justify-between items-center text-text-secondary">
              <span>Phase 1: Sonar Ingestion & Quality Layer</span>
              <span className="font-mono">Pending</span>
            </div>
            <div className="p-2.5 rounded bg-bg-elevated border border-border-subtle flex justify-between items-center text-text-secondary">
              <span>Phase 2: Sonar Preprocessing & Tiler</span>
              <span className="font-mono">Pending</span>
            </div>
            <div className="p-2.5 rounded bg-bg-elevated border border-border-subtle flex justify-between items-center text-text-secondary">
              <span>Phase 3: YOLOv8 Detection & Shadow Filtering</span>
              <span className="font-mono">Pending</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
