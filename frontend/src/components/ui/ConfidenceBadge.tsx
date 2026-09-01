import React from "react";

interface ConfidenceBadgeProps {
  confidence: number;
  calibrated?: number;
}

export const ConfidenceBadge: React.FC<ConfidenceBadgeProps> = ({ confidence, calibrated }) => {
  const score = calibrated !== undefined && calibrated !== null ? calibrated : confidence;
  const pct = Math.round(score * 100);

  let color = "text-emerald-400 border-emerald-500/30 bg-emerald-500/10";
  if (pct < 50) {
    color = "text-red-400 border-red-500/30 bg-red-500/10";
  } else if (pct < 75) {
    color = "text-amber-400 border-amber-500/30 bg-amber-500/10";
  }

  return (
    <div className="flex items-center gap-1.5 font-mono text-xs">
      <span className={`px-2 py-0.5 rounded border font-semibold ${color}`}>
        {pct}%
      </span>
      {calibrated !== undefined && calibrated !== null && (
        <span className="text-[10px] text-text-secondary" title="Calibrated with Platt/Temperature scaling">
          (cal)
        </span>
      )}
    </div>
  );
};
