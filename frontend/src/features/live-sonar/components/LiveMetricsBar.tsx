import React from "react";
import { LiveMetrics } from "../types";
import { Activity, AlertTriangle, Cpu, Layers, ShieldCheck } from "lucide-react";

interface LiveMetricsBarProps {
  metrics: LiveMetrics;
  gpuDevice?: string;
}

export const LiveMetricsBar: React.FC<LiveMetricsBarProps> = ({ metrics, gpuDevice = "CPU" }) => {
  const isBackpressure = metrics.input_fps > metrics.inference_fps && metrics.inference_fps > 0;

  return (
    <div className="w-full bg-bg-surface border border-border-subtle rounded-xl p-3 flex flex-wrap items-center justify-between gap-4 font-mono text-xs shadow-card">
      <div className="flex flex-wrap items-center gap-4">
        {/* Input FPS */}
        <div className="flex items-center gap-1.5">
          <span className="text-text-muted text-[11px]">INPUT</span>
          <span className="font-semibold text-text-primary px-1.5 py-0.5 rounded bg-bg-elevated border border-border-subtle">
            {metrics.input_fps.toFixed(1)} FPS
          </span>
        </div>

        {/* Inference FPS */}
        <div className="flex items-center gap-1.5">
          <span className="text-text-muted text-[11px]">INFERENCE</span>
          <span className="font-semibold text-accent px-1.5 py-0.5 rounded bg-accent/10 border border-accent/20">
            {metrics.inference_fps.toFixed(1)} FPS
          </span>
        </div>

        {/* Display FPS */}
        <div className="flex items-center gap-1.5">
          <span className="text-text-muted text-[11px]">DISPLAY</span>
          <span className="font-semibold text-sonar-teal px-1.5 py-0.5 rounded bg-sonar-teal/10 border border-sonar-teal/20">
            {metrics.display_fps ?? 0} FPS
          </span>
        </div>

        {/* Latency */}
        <div className="flex items-center gap-1.5">
          <span className="text-text-muted text-[11px]">LATENCY</span>
          <span className="font-semibold text-text-primary px-1.5 py-0.5 rounded bg-bg-elevated border border-border-subtle">
            {metrics.latency_ms.toFixed(1)} ms
          </span>
        </div>

        {/* Inference Hardware */}
        <div className="flex items-center gap-1.5">
          <Cpu className="w-3.5 h-3.5 text-text-muted" />
          <span className="text-text-muted text-[11px]">DEVICE</span>
          <span className="font-semibold text-text-secondary px-1.5 py-0.5 rounded bg-bg-elevated border border-border-subtle uppercase">
            {gpuDevice}
          </span>
        </div>
      </div>

      <div className="flex flex-wrap items-center gap-4">
        {/* Backpressure warning badge */}
        {isBackpressure && (
          <div className="flex items-center gap-1 px-2 py-0.5 rounded bg-amber-500/10 border border-amber-500/30 text-amber-700 text-[11px] font-semibold animate-pulse">
            <AlertTriangle className="w-3 h-3 text-amber-600" />
            <span>BACKPRESSURE: ADAPTING</span>
          </div>
        )}

        {/* Queue Depth */}
        <div className="flex items-center gap-1.5">
          <Layers className="w-3.5 h-3.5 text-text-muted" />
          <span className="text-text-muted text-[11px]">QUEUE</span>
          <span className="font-semibold text-text-primary">{metrics.queue_depth}</span>
        </div>

        {/* Dropped Frames */}
        <div className="flex items-center gap-1.5">
          <span className="text-text-muted text-[11px]">DROPPED</span>
          <span className={`font-semibold ${metrics.frames_dropped > 0 ? "text-amber-600" : "text-text-muted"}`}>
            {metrics.frames_dropped}
          </span>
        </div>

        {/* Active Tracks */}
        <div className="flex items-center gap-1.5">
          <Activity className="w-3.5 h-3.5 text-sonar-sky" />
          <span className="text-text-muted text-[11px]">TRACKS</span>
          <span className="font-semibold text-sonar-sky">{metrics.active_tracks}</span>
        </div>

        {/* Confirmed Targets */}
        <div className="flex items-center gap-1.5">
          <ShieldCheck className="w-3.5 h-3.5 text-emerald-600" />
          <span className="text-text-muted text-[11px]">CONFIRMED</span>
          <span className="font-semibold text-emerald-600 px-1.5 py-0.5 rounded bg-emerald-50 border border-emerald-200">
            {metrics.confirmed_targets}
          </span>
        </div>
      </div>
    </div>
  );
};
