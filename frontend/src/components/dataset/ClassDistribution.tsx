import React from "react";
import { ClassDistribution, TaxonomyData, Confident } from "../../types/dataset";
import { ConfidenceStateBadge } from "./ConfidenceStateBadge";
import { BarChart as BarChartIcon } from "lucide-react";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from "recharts";

interface Props {
  distribution: Confident<ClassDistribution[]>;
  taxonomy: Confident<TaxonomyData>;
}

export const ClassDistributionComponent: React.FC<Props> = ({ distribution, taxonomy }) => {
  const { data: distData, confidence } = distribution;
  const { data: taxData } = taxonomy;

  if (!distData) {
    return (
      <div className="p-6 bg-bg-surface border border-border-subtle rounded-2xl shadow-card">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold flex items-center text-text-primary">
            <BarChartIcon className="w-5 h-5 mr-2 text-accent" />
            Class Distribution
          </h2>
          <ConfidenceStateBadge state={confidence} />
        </div>
        <div className="text-sm text-text-secondary">Not Available</div>
      </div>
    );
  }

  const activeClasses = distData.filter(d => d.count > 0).sort((a, b) => b.count - a.count);
  
  // Find zero-count canonical classes
  const canonicalNames = taxData?.canonical_classes?.map(c => c.name) || [];
  const zeroClasses = canonicalNames.filter(
    name => !activeClasses.find(a => a.class_name === name)
  );

  return (
    <div className="p-6 bg-bg-surface border border-border-subtle rounded-2xl shadow-card space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold flex items-center text-text-primary">
          <BarChartIcon className="w-5 h-5 mr-2 text-accent" />
          Class Distribution
        </h2>
        <ConfidenceStateBadge state={confidence} />
      </div>

      <div className="h-80 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={activeClasses} layout="vertical" margin={{ top: 5, right: 30, left: 100, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" horizontal={true} vertical={true} stroke="#E2E8F0" />
            <XAxis type="number" tick={{ fontSize: 12, fill: "#64748B" }} />
            <YAxis 
              dataKey="class_name" 
              type="category" 
              tick={{ fontSize: 11, fill: "#475569" }}
              width={150}
            />
            <Tooltip 
              cursor={{ fill: '#F1F5F9' }}
              contentStyle={{ borderRadius: '8px', border: '1px solid #E2E8F0', boxShadow: '0 4px 6px -1px rgba(15, 23, 42, 0.08)' }}
            />
            <Bar dataKey="count" radius={[0, 4, 4, 0]}>
              {activeClasses.map((_, index) => (
                <Cell key={`cell-${index}`} fill="#0284C7" />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>

      {zeroClasses.length > 0 && (
        <div className="mt-8 pt-6 border-t border-border-subtle">
          <h3 className="text-xs font-bold text-text-muted uppercase tracking-wider mb-4">
            CANONICAL CLASSES NOT REPRESENTED IN BENCHMARK
          </h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3">
            {zeroClasses.map(zc => (
              <div key={zc} className="p-3 bg-slate-50 border border-slate-200 rounded-lg flex flex-col">
                <span className="font-semibold text-sm text-slate-700 mb-1">{zc}</span>
                <span className="text-[10px] font-mono text-rose-600 bg-rose-50 px-2 py-0.5 rounded w-fit border border-rose-100">
                  MODEL PERFORMANCE NOT ESTABLISHED
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
