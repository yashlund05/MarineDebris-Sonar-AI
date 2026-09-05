import React from "react";
import { Gauge, Target, Sliders } from "lucide-react";
import { ModelMetricsResponse } from "../../types/modelEvaluation";

interface MetricSummaryProps {
  metricsResponse: ModelMetricsResponse;
}

export const MetricSummary: React.FC<MetricSummaryProps> = ({ metricsResponse }) => {
  const canonical = metricsResponse.metrics.canonical_benchmark;
  const operational = metricsResponse.metrics.operational_point;

  const formatPct = (val?: number | null) => {
    if (val === undefined || val === null) return "N/A";
    return `${(val * 100).toFixed(2)}%`;
  };

  const formatNum = (val?: number | null, decimals = 4) => {
    if (val === undefined || val === null) return "N/A";
    return val.toFixed(decimals);
  };

  return (
    <div className="bg-bg-surface border border-border-subtle rounded-2xl p-6 shadow-card space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-border-subtle pb-4">
        <div>
          <div className="flex items-center gap-2 text-xs font-semibold text-accent uppercase tracking-wider font-mono">
            <Gauge className="w-3.5 h-3.5" />
            Detection Performance Intelligence
          </div>
          <h3 className="text-base font-bold text-text-primary mt-0.5">
            Evaluated Detection Metrics & Threshold Regimes
          </h3>
        </div>
        <div className="flex items-center gap-2">
          <span className="px-2.5 py-1 bg-emerald-50 border border-emerald-200 text-emerald-800 rounded-full text-xs font-mono font-semibold">
            {metricsResponse.confidence}
          </span>
          <span className="text-xs text-text-muted font-mono">
            Split: {canonical?.evaluation_split || "test"}
          </span>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Canonical Benchmark Card */}
        <div className="p-5 bg-slate-50 border border-border-subtle rounded-xl space-y-4">
          <div className="flex items-center justify-between border-b border-border-subtle pb-2.5">
            <div className="flex items-center gap-2">
              <Target className="w-4 h-4 text-accent" />
              <h4 className="text-xs font-bold font-mono text-text-primary uppercase tracking-wide">
                Canonical Research Benchmark
              </h4>
            </div>
            <span className="text-[11px] font-mono bg-white px-2 py-0.5 rounded border border-border-subtle text-text-secondary">
              conf={canonical?.confidence_threshold ?? 0.001}, IoU={canonical?.iou_threshold ?? 0.70}
            </span>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <div className="p-3 bg-white rounded-lg border border-border-subtle">
              <span className="text-[11px] text-text-muted font-mono block">mAP@50</span>
              <span className="text-base font-mono font-bold text-accent">
                {formatPct(canonical?.map50)}
              </span>
            </div>
            <div className="p-3 bg-white rounded-lg border border-border-subtle">
              <span className="text-[11px] text-text-muted font-mono block">mAP@50-95</span>
              <span className="text-base font-mono font-bold text-text-primary">
                {formatPct(canonical?.map50_95)}
              </span>
            </div>
            <div className="p-3 bg-white rounded-lg border border-border-subtle">
              <span className="text-[11px] text-text-muted font-mono block">Recall</span>
              <span className="text-base font-mono font-bold text-text-primary">
                {formatPct(canonical?.recall)}
              </span>
            </div>
            <div className="p-3 bg-white rounded-lg border border-border-subtle">
              <span className="text-[11px] text-text-muted font-mono block">Precision</span>
              <span className="text-base font-mono font-bold text-text-primary">
                {formatPct(canonical?.precision)}
              </span>
            </div>
          </div>
          <p className="text-[11px] text-text-muted leading-relaxed">
            Standard literature-standard benchmark evaluation regime capturing maximal recall and acoustic curve area without operational filtering.
          </p>
        </div>

        {/* Operational Point Card */}
        <div className="p-5 bg-slate-50 border border-border-subtle rounded-xl space-y-4">
          <div className="flex items-center justify-between border-b border-border-subtle pb-2.5">
            <div className="flex items-center gap-2">
              <Sliders className="w-4 h-4 text-blue-600" />
              <h4 className="text-xs font-bold font-mono text-text-primary uppercase tracking-wide">
                Operational In-Water Point
              </h4>
            </div>
            <span className="text-[11px] font-mono bg-white px-2 py-0.5 rounded border border-border-subtle text-text-secondary">
              conf={operational?.confidence_threshold ?? 0.25}, IoU={operational?.iou_threshold ?? 0.45}
            </span>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <div className="p-3 bg-white rounded-lg border border-border-subtle">
              <span className="text-[11px] text-text-muted font-mono block">Precision</span>
              <span className="text-base font-mono font-bold text-emerald-700">
                {formatPct(operational?.precision)}
              </span>
            </div>
            <div className="p-3 bg-white rounded-lg border border-border-subtle">
              <span className="text-[11px] text-text-muted font-mono block">Recall</span>
              <span className="text-base font-mono font-bold text-text-primary">
                {formatPct(operational?.recall)}
              </span>
            </div>
            <div className="p-3 bg-white rounded-lg border border-border-subtle">
              <span className="text-[11px] text-text-muted font-mono block">F1-Score</span>
              <span className="text-base font-mono font-bold text-blue-700">
                {formatNum(operational?.f1)}
              </span>
            </div>
            <div className="p-3 bg-white rounded-lg border border-border-subtle">
              <span className="text-[11px] text-text-muted font-mono block">mAP@50</span>
              <span className="text-base font-mono font-bold text-text-primary">
                {formatPct(operational?.map50)}
              </span>
            </div>
          </div>
          <p className="text-[11px] text-text-muted leading-relaxed">
            Realistic ROV/AUV acoustic deployment operating threshold designed to suppress seabed reverberation and speckle noise.
          </p>
        </div>
      </div>
    </div>
  );
};
