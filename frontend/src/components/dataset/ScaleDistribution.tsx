import React from "react";
import { ScaleDistribution, Confident } from "../../types/dataset";
import { ConfidenceStateBadge } from "./ConfidenceStateBadge";
import { Maximize } from "lucide-react";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from "recharts";

interface Props {
  scale_distribution: Confident<ScaleDistribution[]>;
}

export const ScaleDistributionComponent: React.FC<Props> = ({ scale_distribution }) => {
  const { data, confidence } = scale_distribution;

  if (!data) {
    return (
      <div className="p-6 bg-bg-surface border border-border-subtle rounded-2xl shadow-card">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold flex items-center text-text-primary">
            <Maximize className="w-5 h-5 mr-2 text-accent" />
            Scale Distribution
          </h2>
          <ConfidenceStateBadge state={confidence} />
        </div>
        <div className="text-sm text-text-secondary">Not Available</div>
      </div>
    );
  }

  // Define scale order and colors
  const order = ["Tiny", "Small", "Medium", "Large"];
  const colors: Record<string, string> = {
    "Tiny": "#94A3B8", // slate-400
    "Small": "#0EA5E9", // sky-500
    "Medium": "#3B82F6", // blue-500
    "Large": "#4F46E5", // indigo-600
  };

  const sortedData = [...data].sort((a, b) => {
    return order.indexOf(a.scale) - order.indexOf(b.scale);
  });

  return (
    <div className="p-6 bg-bg-surface border border-border-subtle rounded-2xl shadow-card space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold flex items-center text-text-primary">
          <Maximize className="w-5 h-5 mr-2 text-accent" />
          Scale Distribution
        </h2>
        <ConfidenceStateBadge state={confidence} />
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        {sortedData.map((item, idx) => (
          <div key={idx} className="p-3 bg-bg-elevated border border-border-subtle rounded-xl text-center">
            <div className="text-sm font-semibold text-text-primary mb-1">{item.scale}</div>
            <div className="text-[10px] text-text-muted font-mono bg-bg-surface border border-border-subtle rounded px-1.5 py-0.5 mx-auto w-fit mb-2">
              {item.definition}
            </div>
            <div className="text-lg font-mono font-bold text-text-primary">
              {item.count.toLocaleString()}
            </div>
          </div>
        ))}
      </div>

      <div className="h-64 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={sortedData} margin={{ top: 10, right: 30, left: 0, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#E2E8F0" />
            <XAxis dataKey="scale" tick={{ fontSize: 12, fill: "#475569" }} />
            <YAxis tick={{ fontSize: 12, fill: "#64748B" }} width={80} />
            <Tooltip 
              cursor={{ fill: '#F1F5F9' }}
              contentStyle={{ borderRadius: '8px', border: '1px solid #E2E8F0', boxShadow: '0 4px 6px -1px rgba(15, 23, 42, 0.08)' }}
            />
            <Bar dataKey="count" radius={[4, 4, 0, 0]}>
              {sortedData.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={colors[entry.scale] || "#0284C7"} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};
