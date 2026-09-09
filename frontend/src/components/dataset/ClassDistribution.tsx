import React from "react";
import { ClassDistribution, TaxonomyData, Confident, CanonicalAuditData } from "../../types/dataset";
import { ConfidenceStateBadge } from "./ConfidenceStateBadge";
import { BarChart as BarChartIcon } from "lucide-react";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from "recharts";
import { clsx } from "clsx";

interface Props {
  distribution: Confident<ClassDistribution[]>;
  taxonomy: Confident<TaxonomyData>;
  canonicalAudit?: Confident<CanonicalAuditData>;
}

export const ClassDistributionComponent: React.FC<Props> = ({ distribution, taxonomy, canonicalAudit }) => {
  const { data: distData, confidence } = distribution;
  const { data: taxData } = taxonomy;
  const auditData = canonicalAudit?.data;

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
  
  // Find zero-count canonical classes if auditData is not present
  const canonicalNames = taxData?.canonical_classes?.map(c => c.name) || [];
  const zeroClasses = canonicalNames.filter(
    name => !activeClasses.find(a => a.class_name === name)
  );

  return (
    <div className="p-6 bg-bg-surface border border-border-subtle rounded-2xl shadow-card space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold flex items-center text-text-primary">
            <BarChartIcon className="w-5 h-5 mr-2 text-accent" />
            Class Distribution & Canonical Audit
          </h2>
          <p className="text-xs text-text-secondary mt-0.5">
            Real acoustic ground-truth sample distribution and canonical taxonomy verification
          </p>
        </div>
        <ConfidenceStateBadge state={confidence} />
      </div>

      <div className="h-80 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={activeClasses} layout="vertical" margin={{ top: 5, right: 30, left: 120, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" horizontal={true} vertical={true} stroke="#E2E8F0" />
            <XAxis type="number" tick={{ fontSize: 12, fill: "#64748B" }} />
            <YAxis 
              dataKey="class_name" 
              type="category" 
              tick={{ fontSize: 11, fill: "#475569" }}
              width={160}
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

      {/* Dynamic Canonical Class Audit Cards */}
      {auditData?.canonical_classes && auditData.canonical_classes.length > 0 ? (
        <div className="mt-8 pt-6 border-t border-border-subtle space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-xs font-bold text-text-muted uppercase tracking-wider">
                CANONICAL TAXONOMY AUDIT & MULTI-CLASS BENCHMARK STATUS
              </h3>
              <p className="text-[11px] text-text-secondary mt-0.5">
                Evaluated against frozen detector (SHA256: {auditData.production_model?.sha256?.substring(0, 16) || "e1215c7e"}...)
              </p>
            </div>
            <div className="text-[10px] font-mono text-slate-500 bg-slate-100 px-2.5 py-1 rounded-md border border-slate-200">
              5 Canonical Classes Audited
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {auditData.canonical_classes.map((cls) => {
              const isEstablished = cls.benchmark_status === "ESTABLISHED";
              const isProvisional = cls.benchmark_status === "PROVISIONAL";
              const isRestricted = cls.benchmark_status === "RESTRICTED";
              
              const statusBadgeStyle = isEstablished
                ? "bg-emerald-50 text-emerald-700 border-emerald-200"
                : isProvisional
                ? "bg-amber-50 text-amber-800 border-amber-200"
                : isRestricted
                ? "bg-purple-50 text-purple-700 border-purple-200"
                : "bg-rose-50 text-rose-700 border-rose-200";

              return (
                <div 
                  key={cls.class_id}
                  className="p-4 bg-slate-50/70 border border-slate-200 rounded-xl flex flex-col justify-between space-y-3 hover:border-slate-300 transition-colors"
                >
                  <div>
                    <div className="flex items-start justify-between gap-2 mb-1.5">
                      <div className="flex items-center gap-1.5">
                        <span className="w-5 h-5 rounded-full bg-slate-200 text-slate-700 text-[10px] font-mono font-bold flex items-center justify-center">
                          {cls.class_id}
                        </span>
                        <span className="font-semibold text-sm text-slate-900 leading-tight">
                          {cls.class_name}
                        </span>
                      </div>
                      <span className={clsx("text-[10px] font-mono font-bold px-2 py-0.5 rounded border whitespace-nowrap", statusBadgeStyle)}>
                        {cls.benchmark_status}
                      </span>
                    </div>

                    <p className="text-[11px] text-slate-600 line-clamp-2 mb-2.5">
                      {cls.description}
                    </p>

                    <div className="grid grid-cols-2 gap-2 text-[10px] font-mono bg-white p-2 rounded-lg border border-slate-200/80 mb-2.5">
                      <div>
                        <span className="text-slate-400 block text-[9px] uppercase">Evaluation Data</span>
                        <span className="font-semibold text-slate-800">{cls.sample_count} {cls.modality} frames</span>
                      </div>
                      <div>
                        <span className="text-slate-400 block text-[9px] uppercase">Sensor Physics</span>
                        <span className="font-semibold text-slate-800 truncate block" title={cls.sensor}>{cls.sensor.split("(")[0]}</span>
                      </div>
                      <div>
                        <span className="text-slate-400 block text-[9px] uppercase">Model Detection</span>
                        <span className={clsx("font-semibold block truncate", isEstablished ? "text-emerald-700" : "text-rose-600")}>
                          {cls.model_status.replace(/_/g, " ")}
                        </span>
                      </div>
                      <div>
                        <span className="text-slate-400 block text-[9px] uppercase">mAP50 Baseline</span>
                        <span className="font-semibold text-slate-800">{(cls.ap50 * 100).toFixed(1)}%</span>
                      </div>
                    </div>
                  </div>

                  <div className="pt-2 border-t border-slate-200/60 text-[10px] text-slate-500 flex flex-col gap-1">
                    <div className="flex items-center justify-between">
                      <span className="font-medium text-slate-700">Source: {cls.source_dataset.split("(")[0]}</span>
                      <span className="font-mono text-[9px] text-slate-400">{cls.license}</span>
                    </div>
                    {cls.secondary_source && (
                      <div className="text-[9px] text-purple-700 font-medium bg-purple-50 px-1.5 py-0.5 rounded border border-purple-100 truncate" title={cls.secondary_source}>
                        Aux: {cls.secondary_source}
                      </div>
                    )}
                    <div className="text-[9px] text-slate-500 italic mt-0.5">
                      {cls.recommendation}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      ) : zeroClasses.length > 0 ? (
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
      ) : null}
    </div>
  );
};

