import React from "react";
import { OverviewData, Confident } from "../../types/dataset";
import { ConfidenceStateBadge } from "./ConfidenceStateBadge";
import { Database, Image as ImageIcon, Crosshair, Activity, Layers } from "lucide-react";

interface Props {
  overview: Confident<OverviewData>;
}

export const DatasetOverview: React.FC<Props> = ({ overview }) => {
  const { data, confidence } = overview;

  if (!data) {
    return (
      <div className="p-6 bg-bg-surface border border-border-subtle rounded-2xl shadow-card">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold flex items-center text-text-primary">
            <Database className="w-5 h-5 mr-2 text-accent" />
            Dataset Overview
          </h2>
          <ConfidenceStateBadge state={confidence} />
        </div>
        <div className="text-sm text-text-secondary">Not Available</div>
      </div>
    );
  }

  const stats = [
    { label: "Total Images", value: data.total_images, icon: ImageIcon, color: "text-sky-600" },
    { label: "Total Annotations", value: data.total_annotations, icon: Crosshair, color: "text-emerald-600" },
    { label: "Total Sequences", value: data.total_sequences, icon: Layers, color: "text-amber-600" },
    { label: "Total Positives", value: data.total_positives, icon: Activity, color: "text-rose-600" },
    { label: "Total Negatives", value: data.total_negatives, icon: Database, color: "text-slate-600" },
  ];

  return (
    <div className="p-6 bg-bg-surface border border-border-subtle rounded-2xl shadow-card space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold flex items-center text-text-primary">
          <Database className="w-5 h-5 mr-2 text-accent" />
          Dataset Overview
        </h2>
        <div className="flex items-center gap-3">
          {data.status_badge && (
            <span className="px-2.5 py-1 text-xs font-semibold rounded-md bg-accent-subtle text-accent border border-blue-200">
              {data.status_badge}
            </span>
          )}
          <ConfidenceStateBadge state={confidence} />
        </div>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
        {stats.map((stat, idx) => (
          <div key={idx} className="p-4 rounded-xl border border-border-subtle bg-bg-elevated flex flex-col items-center text-center">
            <stat.icon className={`w-6 h-6 mb-2 ${stat.color}`} />
            <div className="text-2xl font-mono font-bold text-text-primary">
              {stat.value !== undefined && stat.value !== null ? stat.value.toLocaleString() : "N/A"}
            </div>
            <div className="text-xs font-medium text-text-secondary uppercase tracking-wide mt-1">
              {stat.label}
            </div>
          </div>
        ))}
      </div>

      {data.integrity_statement && (
        <div className="p-4 bg-slate-50 border-l-4 border-slate-400 text-sm text-slate-700 rounded-r-lg">
          <span className="font-semibold block mb-1">Integrity Statement:</span>
          {data.integrity_statement}
        </div>
      )}
    </div>
  );
};
