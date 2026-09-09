import React, { useState } from "react";
import {
  Activity,
  TrendingUp,
  FileCode2,
  ChevronDown,
  ChevronUp,
  Clock,
  ShieldCheck,
} from "lucide-react";
import { ComparativeMetrics } from "../../types/sonarEnhancement";

interface QualityDiagnosticsCardProps {
  metrics: ComparativeMetrics;
  auditTrail: string[];
  appliedOperations: string[];
  executionTimeMs: number;
  rawSha256: string;
}

export const QualityDiagnosticsCard: React.FC<QualityDiagnosticsCardProps> = ({
  metrics,
  auditTrail,
  appliedOperations,
  executionTimeMs,
  rawSha256,
}) => {
  const [showAudit, setShowAudit] = useState<boolean>(false);

  const delta = metrics.delta;
  const raw = metrics.raw;
  const enh = metrics.enhanced;

  return (
    <div className="bg-bg-surface border border-border-subtle rounded-2xl p-5 shadow-sm space-y-4">
      {/* Applied operations pills */}
      <div className="flex flex-wrap items-center gap-1.5 pb-1">
        <span className="text-[10px] text-text-muted font-medium">Applied:</span>
        {appliedOperations.map((op, idx) => (
          <span key={idx} className="px-2 py-0.5 rounded-full text-[10px] font-mono bg-accent-subtle/40 text-accent font-medium">
            {op}
          </span>
        ))}
      </div>

      {/* Header */}
      <div className="flex items-center justify-between border-b border-border-subtle pb-3">
        <div className="flex items-center gap-2">
          <Activity className="w-4 h-4 text-emerald-600" />
          <h3 className="font-semibold text-sm text-text-primary">Acoustic Quality Diagnostics</h3>
        </div>
        <div className="flex items-center gap-1.5 font-mono text-[11px] text-text-muted bg-bg-elevated px-2.5 py-1 rounded-lg">
          <Clock className="w-3 h-3 text-text-muted" />
          <span>{executionTimeMs} ms</span>
        </div>
      </div>

      {/* Metrics Grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {/* RMS Contrast */}
        <div className="p-3 bg-bg-elevated/50 border border-border-subtle rounded-xl flex flex-col justify-between">
          <div className="text-[11px] text-text-muted font-medium">RMS Contrast</div>
          <div className="my-1 flex items-baseline gap-2">
            <span className="font-mono text-base font-bold text-text-primary">{enh.rms_contrast}</span>
            <span className="text-[10px] font-mono text-text-muted">({raw.rms_contrast})</span>
          </div>
          <div className="text-[10px] font-mono font-semibold text-emerald-600 flex items-center gap-1">
            <TrendingUp className="w-3 h-3" />
            <span>{delta.contrast_gain >= 0 ? `+${delta.contrast_gain}` : delta.contrast_gain} gain</span>
          </div>
        </div>

        {/* Shannon Entropy */}
        <div className="p-3 bg-bg-elevated/50 border border-border-subtle rounded-xl flex flex-col justify-between">
          <div className="text-[11px] text-text-muted font-medium">Shannon Entropy</div>
          <div className="my-1 flex items-baseline gap-2">
            <span className="font-mono text-base font-bold text-text-primary">{enh.entropy}</span>
            <span className="text-[10px] font-mono text-text-muted">bits/px</span>
          </div>
          <div className="text-[10px] font-mono font-semibold text-sky-600">
            {delta.entropy_delta >= 0 ? `+${delta.entropy_delta}` : delta.entropy_delta} delta
          </div>
        </div>

        {/* Focus / Sharpness Ratio */}
        <div className="p-3 bg-bg-elevated/50 border border-border-subtle rounded-xl flex flex-col justify-between">
          <div className="text-[11px] text-text-muted font-medium">Tenengrad Sharpness</div>
          <div className="my-1 flex items-baseline gap-2">
            <span className="font-mono text-base font-bold text-text-primary">{delta.sharpness_ratio}x</span>
            <span className="text-[10px] font-mono text-text-muted">ratio</span>
          </div>
          <div className="text-[10px] font-mono text-text-secondary">
            Brenner: {enh.brenner_gradient}
          </div>
        </div>

        {/* Dynamic Range */}
        <div className="p-3 bg-bg-elevated/50 border border-border-subtle rounded-xl flex flex-col justify-between">
          <div className="text-[11px] text-text-muted font-medium">Dynamic Range (P99-P1)</div>
          <div className="my-1 flex items-baseline gap-2">
            <span className="font-mono text-base font-bold text-text-primary">{enh.dynamic_range}</span>
            <span className="text-[10px] font-mono text-text-muted">span</span>
          </div>
          <div className="text-[10px] font-mono text-emerald-600 font-semibold">
            {delta.dynamic_range_gain >= 0 ? `+${delta.dynamic_range_gain}` : delta.dynamic_range_gain} spread
          </div>
        </div>
      </div>

      {/* Raw Preservation Badge */}
      <div className="p-3 bg-emerald-500/10 border border-emerald-500/20 rounded-xl flex items-center justify-between text-xs">
        <div className="flex items-center gap-2 text-emerald-800">
          <ShieldCheck className="w-4 h-4 text-emerald-600 flex-shrink-0" />
          <span className="font-medium">Raw Acoustic Frame Preservation:</span>
          <span className="font-mono text-[11px] text-emerald-700 font-semibold">Verified Byte-Identical</span>
        </div>
        <div className="font-mono text-[10px] text-emerald-800/80 bg-emerald-500/10 px-2 py-0.5 rounded">
          SHA256: {rawSha256.slice(0, 12)}...
        </div>
      </div>

      {/* Collapsible Provenance & Audit Trail */}
      <div className="pt-1">
        <button
          type="button"
          onClick={() => setShowAudit(!showAudit)}
          className="flex items-center justify-between w-full text-xs font-medium text-text-muted hover:text-text-secondary transition py-1"
        >
          <div className="flex items-center gap-1.5">
            <FileCode2 className="w-3.5 h-3.5" />
            <span>Scientific Provenance & Audit Trail ({auditTrail.length} steps)</span>
          </div>
          {showAudit ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
        </button>

        {showAudit && (
          <div className="mt-2.5 p-3 rounded-xl bg-bg-elevated/70 border border-border-subtle text-xs space-y-1.5 font-mono text-[11px] text-text-secondary">
            {auditTrail.map((log, i) => (
              <div key={i} className="flex items-start gap-2">
                <span className="text-text-muted">{i + 1}.</span>
                <span>{log}</span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
