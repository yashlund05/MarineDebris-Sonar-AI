import React from "react";
import { GitBranch } from "lucide-react";
import { RegisteredModelSummary } from "../../types/modelEvaluation";

interface ExperimentSelectorProps {
  models: RegisteredModelSummary[];
  selectedModelId: string;
  onSelectModel: (modelId: string) => void;
}

export const ExperimentSelector: React.FC<ExperimentSelectorProps> = ({
  models,
  selectedModelId,
  onSelectModel,
}) => {
  return (
    <div className="bg-bg-surface border border-border-subtle rounded-2xl p-4 shadow-card flex flex-col md:flex-row md:items-center justify-between gap-4">
      <div className="flex items-center gap-3">
        <div className="p-2.5 bg-accent/10 rounded-xl text-accent">
          <GitBranch className="w-5 h-5" />
        </div>
        <div>
          <h3 className="text-sm font-bold text-text-primary">Evaluation Model & Checkpoint Selection</h3>
          <p className="text-xs text-text-secondary">
            Switch between production baseline, experimental candidates, and multi-seed robustness suites.
          </p>
        </div>
      </div>

      <div className="flex items-center gap-2">
        <select
          value={selectedModelId}
          onChange={(e) => onSelectModel(e.target.value)}
          className="bg-bg-elevated border border-border-subtle rounded-xl px-4 py-2 text-xs font-mono font-medium text-text-primary focus:outline-none focus:ring-2 focus:ring-accent/40"
        >
          {models.map((m) => (
            <option key={m.id} value={m.id}>
              {m.name} ({m.is_active ? "Production Active" : m.status})
            </option>
          ))}
        </select>
      </div>
    </div>
  );
};
