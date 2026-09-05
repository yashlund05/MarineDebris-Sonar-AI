import React from "react";
import { SplitStats, Confident } from "../../types/dataset";
import { ConfidenceStateBadge } from "./ConfidenceStateBadge";
import { PieChart } from "lucide-react";

interface Props {
  splits: Confident<SplitStats>;
}

export const SplitDistribution: React.FC<Props> = ({ splits }) => {
  const { data, confidence } = splits;

  if (!data) {
    return (
      <div className="p-6 bg-bg-surface border border-border-subtle rounded-2xl shadow-card">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold flex items-center text-text-primary">
            <PieChart className="w-5 h-5 mr-2 text-accent" />
            Split Distribution
          </h2>
          <ConfidenceStateBadge state={confidence} />
        </div>
        <div className="text-sm text-text-secondary">Not Available</div>
      </div>
    );
  }

  const { train, val, test } = data;

  const totalImages = (train?.images || 0) + (val?.images || 0) + (test?.images || 0);

  const getPct = (val: number) => (totalImages > 0 ? ((val / totalImages) * 100).toFixed(1) : "0.0");

  const renderBar = (label: string, stats: any, colorClass: string) => (
    <div className="mb-4 last:mb-0">
      <div className="flex justify-between text-sm mb-1.5">
        <span className="font-semibold text-text-primary uppercase">{label}</span>
        <span className="font-mono font-medium text-text-secondary">
          {stats?.images?.toLocaleString() ?? 0} images ({getPct(stats?.images || 0)}%)
        </span>
      </div>
      <div className="w-full bg-bg-subtle rounded-full h-3 mb-2 overflow-hidden border border-border-subtle">
        <div
          className={`h-3 rounded-full ${colorClass}`}
          style={{ width: `${getPct(stats?.images || 0)}%` }}
        ></div>
      </div>
      <div className="flex gap-4 text-[11px] text-text-muted font-mono">
        <span>Annots: {stats?.annotations?.toLocaleString() ?? 0}</span>
        <span>Negatives: {stats?.negatives?.toLocaleString() ?? 0}</span>
      </div>
    </div>
  );

  return (
    <div className="p-6 bg-bg-surface border border-border-subtle rounded-2xl shadow-card space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold flex items-center text-text-primary">
          <PieChart className="w-5 h-5 mr-2 text-accent" />
          Split Distribution
        </h2>
        <ConfidenceStateBadge state={confidence} />
      </div>

      <div className="space-y-6">
        {renderBar("Train", train, "bg-sky-500")}
        {renderBar("Validation", val, "bg-amber-500")}
        {renderBar("Test", test, "bg-emerald-500")}
      </div>
    </div>
  );
};
