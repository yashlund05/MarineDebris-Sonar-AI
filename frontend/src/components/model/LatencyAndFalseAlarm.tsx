import React from "react";
import { AlertTriangle, Clock } from "lucide-react";
import { ModelMetricsResponse } from "../../types/modelEvaluation";

interface LatencyAndFalseAlarmProps {
  metricsResponse: ModelMetricsResponse;
}

export const LatencyAndFalseAlarm: React.FC<LatencyAndFalseAlarmProps> = ({ metricsResponse }) => {
  const hardNegatives = metricsResponse.metrics.hard_negatives;
  const latency = metricsResponse.metrics.latency_profile;

  const p95 = latency?.latency_p95_ms;
  const meetsBudget = p95 ? p95 <= 125.0 : false;

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      {/* False Alarm Analysis */}
      <div className="bg-bg-surface border border-border-subtle rounded-2xl p-6 shadow-card space-y-4">
        <div className="flex items-center justify-between border-b border-border-subtle pb-3">
          <div className="flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 text-amber-600" />
            <h3 className="text-sm font-bold text-text-primary">
              Hard-Negative Clutter & False Alarm Analysis
            </h3>
          </div>
          <span className="text-xs font-mono px-2.5 py-0.5 rounded-full bg-slate-100 border border-slate-200 text-text-secondary">
            84 Quarry Frames
          </span>
        </div>

        <div className="grid grid-cols-3 gap-3">
          <div className="p-3 bg-slate-50 border border-border-subtle rounded-xl">
            <span className="text-[11px] text-text-muted font-mono block">False Alarm Rate</span>
            <span className="text-lg font-mono font-bold text-amber-700">
              {hardNegatives?.far !== undefined && hardNegatives?.far !== null
                ? `${(hardNegatives.far * 100).toFixed(2)}%`
                : "N/A"}
            </span>
          </div>

          <div className="p-3 bg-slate-50 border border-border-subtle rounded-xl">
            <span className="text-[11px] text-text-muted font-mono block">False Positives</span>
            <span className="text-lg font-mono font-bold text-text-primary">
              {hardNegatives?.false_positive_count ?? "N/A"}
            </span>
          </div>

          <div className="p-3 bg-slate-50 border border-border-subtle rounded-xl">
            <span className="text-[11px] text-text-muted font-mono block">Baseline (E0) FAR</span>
            <span className="text-lg font-mono font-bold text-text-muted">
              21.43%
            </span>
          </div>
        </div>

        <p className="text-xs text-text-secondary leading-relaxed">
          Tested against confirmed debris-free seabed environments with high acoustic reverberation and boulder shadows. Evaluates acoustic hallucination resistance.
        </p>
      </div>

      {/* Latency Profile */}
      <div className="bg-bg-surface border border-border-subtle rounded-2xl p-6 shadow-card space-y-4">
        <div className="flex items-center justify-between border-b border-border-subtle pb-3">
          <div className="flex items-center gap-2">
            <Clock className="w-4 h-4 text-accent" />
            <h3 className="text-sm font-bold text-text-primary">
              CPU Latency & Real-Time Acoustic Budget
            </h3>
          </div>
          <span
            className={`text-xs font-mono px-2.5 py-0.5 rounded-full border ${
              meetsBudget
                ? "bg-emerald-50 border-emerald-200 text-emerald-800"
                : "bg-rose-50 border-rose-200 text-rose-800"
            }`}
          >
            Budget: ≤ 125.0 ms P95
          </span>
        </div>

        <div className="grid grid-cols-4 gap-2.5">
          <div className="p-3 bg-slate-50 border border-border-subtle rounded-xl">
            <span className="text-[11px] text-text-muted font-mono block">Mean</span>
            <span className="text-sm font-mono font-bold text-text-primary">
              {latency?.latency_mean_ms ? `${latency.latency_mean_ms.toFixed(1)} ms` : "N/A"}
            </span>
          </div>

          <div className="p-3 bg-slate-50 border border-border-subtle rounded-xl">
            <span className="text-[11px] text-text-muted font-mono block">P50</span>
            <span className="text-sm font-mono font-bold text-text-primary">
              {latency?.latency_p50_ms ? `${latency.latency_p50_ms.toFixed(1)} ms` : "N/A"}
            </span>
          </div>

          <div className="p-3 bg-slate-50 border border-border-subtle rounded-xl">
            <span className="text-[11px] text-text-muted font-mono block">P95</span>
            <span
              className={`text-sm font-mono font-bold ${
                meetsBudget ? "text-emerald-700" : "text-rose-700"
              }`}
            >
              {latency?.latency_p95_ms ? `${latency.latency_p95_ms.toFixed(1)} ms` : "N/A"}
            </span>
          </div>

          <div className="p-3 bg-slate-50 border border-border-subtle rounded-xl">
            <span className="text-[11px] text-text-muted font-mono block">Throughput</span>
            <span className="text-sm font-mono font-bold text-accent">
              {latency?.throughput ? `${latency.throughput.toFixed(1)} FPS` : "N/A"}
            </span>
          </div>
        </div>

        <p className="text-xs text-text-secondary leading-relaxed">
          Measured on standard Edge CPU (Intel/AMD x86_64) using forward-looking sonar frame resolution (640x640). Real-time sonar acquisition operates at 8–10 Hz.
        </p>
      </div>
    </div>
  );
};
