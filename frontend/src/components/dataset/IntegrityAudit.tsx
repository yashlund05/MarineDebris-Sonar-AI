import React from "react";
import { IntegrityData, Confident } from "../../types/dataset";
import { ConfidenceStateBadge } from "./ConfidenceStateBadge";
import { ShieldAlert, CheckCircle, AlertTriangle } from "lucide-react";

interface Props {
  integrity: Confident<IntegrityData>;
}

export const IntegrityAudit: React.FC<Props> = ({ integrity }) => {
  const { data, confidence } = integrity;

  if (!data) {
    return (
      <div className="p-6 bg-bg-surface border border-border-subtle rounded-2xl shadow-card">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold flex items-center text-text-primary">
            <ShieldAlert className="w-5 h-5 mr-2 text-accent" />
            Integrity Audit
          </h2>
          <ConfidenceStateBadge state={confidence} />
        </div>
        <div className="text-sm text-text-secondary">Not Available</div>
      </div>
    );
  }

  const items = [
    { label: "Leakage Status", value: data.leakage_status },
    { label: "Deduplication Accounting", value: data.dedup_accounting },
    { label: "Annotation Errors", value: data.annotation_errors },
  ];

  const isPass = (val: string) => val.toLowerCase().includes("pass") || val.toLowerCase().includes("zero") || val.toLowerCase().includes("no ");

  return (
    <div className="p-6 bg-bg-surface border border-border-subtle rounded-2xl shadow-card space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold flex items-center text-text-primary">
          <ShieldAlert className="w-5 h-5 mr-2 text-accent" />
          Integrity Audit
        </h2>
        <ConfidenceStateBadge state={confidence} />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {items.map((item, idx) => (
          <div key={idx} className="p-4 bg-bg-elevated border border-border-subtle rounded-xl flex items-start gap-3">
            {isPass(item.value) ? (
              <CheckCircle className="w-5 h-5 text-emerald-500 mt-0.5 shrink-0" />
            ) : (
              <AlertTriangle className="w-5 h-5 text-amber-500 mt-0.5 shrink-0" />
            )}
            <div>
              <div className="text-[11px] font-bold text-text-muted uppercase tracking-wider mb-1">
                {item.label}
              </div>
              <div className="text-sm font-medium text-text-primary">
                {item.value}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
