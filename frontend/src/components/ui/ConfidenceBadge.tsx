import React from "react";

interface ConfidenceBadgeProps {
  confidence: number;
  calibrated?: number;
}

export const ConfidenceBadge: React.FC<ConfidenceBadgeProps> = ({ confidence, calibrated }) => {
  const score = calibrated !== undefined && calibrated !== null ? calibrated : confidence;
  const pct = Math.round(score * 100);

  let color = "text-emerald-700 border-emerald-200 bg-emerald-50";
  if (pct < 50) {
    color = "text-rose-700 border-rose-200 bg-rose-50";
  } else if (pct < 75) {
    color = "text-amber-800 border-amber-200 bg-amber-50";
  }

  return (
    <div className="flex items-center gap-1.5 font-mono text-xs">
      <span className={`px-2 py-0.5 rounded border font-semibold ${color}`}>
        {pct}%
      </span>
      {calibrated !== undefined && calibrated !== null && (
        <span className="text-[10px] text-text-muted" title="Calibrated with temperature scaling">
          (cal)
        </span>
      )}
    </div>
  );
};
