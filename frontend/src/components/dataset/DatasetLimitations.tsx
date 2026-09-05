import React from "react";
import { LimitationData, Confident } from "../../types/dataset";
import { ConfidenceStateBadge } from "./ConfidenceStateBadge";
import { TriangleAlert } from "lucide-react";

interface Props {
  limitations: Confident<LimitationData>;
}

export const DatasetLimitations: React.FC<Props> = ({ limitations }) => {
  const { data, confidence } = limitations;

  if (!data) {
    return (
      <div className="p-6 bg-bg-surface border border-border-subtle rounded-2xl shadow-card">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold flex items-center text-text-primary">
            <TriangleAlert className="w-5 h-5 mr-2 text-accent" />
            Transparent Limitations
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
          <TriangleAlert className="w-5 h-5 mr-2 text-accent" />
          Transparent Limitations
        </h2>
        <ConfidenceStateBadge state={confidence} />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="space-y-4">
          <div>
            <h3 className="text-sm font-semibold text-text-primary mb-1">Single Sensor Bias</h3>
            <p className="text-sm text-text-secondary bg-bg-elevated p-3 rounded-lg border border-border-subtle">
              {data.single_sensor}
            </p>
          </div>
          <div>
            <h3 className="text-sm font-semibold text-text-primary mb-1">Controlled Environment Factors</h3>
            <p className="text-sm text-text-secondary bg-bg-elevated p-3 rounded-lg border border-border-subtle">
              {data.controlled_environment}
            </p>
          </div>
        </div>
        
        <div>
          <h3 className="text-sm font-semibold text-text-primary mb-2">Unrepresented Canonical Classes</h3>
          <ul className="text-sm text-text-secondary bg-rose-50 border border-rose-200 p-4 rounded-lg list-disc pl-5 space-y-1">
            {data.unrepresented_classes?.map((cls, idx) => (
              <li key={idx} className="text-rose-900">{cls}</li>
            ))}
            {(!data.unrepresented_classes || data.unrepresented_classes.length === 0) && (
              <li className="text-emerald-700 list-none">All canonical classes are represented.</li>
            )}
          </ul>
        </div>
      </div>
    </div>
  );
};
