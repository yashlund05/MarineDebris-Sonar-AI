import React from "react";
import { HardNegativeData, Confident } from "../../types/dataset";
import { ConfidenceStateBadge } from "./ConfidenceStateBadge";
import { Ghost } from "lucide-react";

interface Props {
  hard_negatives: Confident<HardNegativeData>;
}

export const HardNegativePanel: React.FC<Props> = ({ hard_negatives }) => {
  const { data, confidence } = hard_negatives;

  if (!data) {
    return (
      <div className="p-6 bg-bg-surface border border-border-subtle rounded-2xl shadow-card">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold flex items-center text-text-primary">
            <Ghost className="w-5 h-5 mr-2 text-accent" />
            Hard Negative Mining
          </h2>
          <ConfidenceStateBadge state={confidence} />
        </div>
        <div className="text-sm text-text-secondary">Not Available</div>
      </div>
    );
  }

  return (
    <div className="p-6 bg-bg-surface border border-border-subtle rounded-2xl shadow-card space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold flex items-center text-text-primary">
          <Ghost className="w-5 h-5 mr-2 text-accent" />
          Hard Negative Mining
        </h2>
        <ConfidenceStateBadge state={confidence} />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="p-4 bg-slate-50 border border-slate-200 rounded-xl">
          <div className="text-sm font-semibold text-slate-800 mb-4">Mining Overview</div>
          <div className="flex flex-col gap-1 mb-4">
            <span className="text-[11px] font-bold text-slate-500 uppercase tracking-wider">Total Verified Negatives</span>
            <span className="text-2xl font-mono font-bold text-slate-900">{data.total_verified_negatives.toLocaleString()}</span>
          </div>
          {data.far_statistics && (
            <div className="flex flex-col gap-1">
              <span className="text-[11px] font-bold text-slate-500 uppercase tracking-wider">False Alarm Rate (FAR) Impact</span>
              <span className="text-sm text-slate-700">{data.far_statistics}</span>
            </div>
          )}
        </div>

        <div className="p-4 bg-bg-elevated border border-border-subtle rounded-xl">
          <div className="text-sm font-semibold text-text-primary mb-4">Domain Breakdown</div>
          <div className="space-y-3">
            {Object.entries(data.breakdown || {}).map(([key, value]) => (
              <div key={key} className="flex items-center justify-between">
                <span className="text-sm text-text-secondary capitalize">{key.replace(/_/g, " ")}</span>
                <span className="font-mono font-medium text-text-primary">{value.toLocaleString()}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};
