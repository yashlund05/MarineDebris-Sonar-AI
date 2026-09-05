import React from "react";
import { Cpu, CheckCircle2, AlertCircle, FileCheck, Layers, Calendar, HardDrive } from "lucide-react";
import { RegisteredModelSummary } from "../../types/modelEvaluation";

interface ModelOverviewCardProps {
  model: RegisteredModelSummary;
}

export const ModelOverviewCard: React.FC<ModelOverviewCardProps> = ({ model }) => {
  return (
    <div className="bg-bg-surface border border-border-subtle rounded-2xl p-6 shadow-card space-y-4">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-border-subtle pb-4">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <span className="text-xs font-mono text-accent uppercase font-bold tracking-wider">
              {model.architecture || "YOLOv8 Nano"}
            </span>
            <span className="text-xs text-text-muted">•</span>
            <span className="text-xs font-mono text-text-muted">{model.framework}</span>
          </div>
          <h2 className="text-xl font-bold text-text-primary tracking-tight">{model.name}</h2>
          <p className="text-xs text-text-secondary font-mono">ID: {model.id}</p>
        </div>

        <div className="flex items-center gap-2 flex-wrap">
          {model.is_active ? (
            <span className="inline-flex items-center gap-1.5 px-3 py-1 bg-emerald-50 border border-emerald-200 text-emerald-800 rounded-full text-xs font-semibold font-mono">
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
              PRODUCTION ACTIVE
            </span>
          ) : (
            <span className="inline-flex items-center gap-1.5 px-3 py-1 bg-amber-50 border border-amber-200 text-amber-800 rounded-full text-xs font-semibold font-mono">
              <AlertCircle className="w-3.5 h-3.5 text-amber-600" />
              {model.status.toUpperCase()}
            </span>
          )}

          <span className="inline-flex items-center gap-1.5 px-3 py-1 bg-blue-50 border border-blue-200 text-blue-800 rounded-full text-xs font-mono">
            <Layers className="w-3.5 h-3.5 text-blue-600" />
            {model.dataset_version || "v3.0.0"}
          </span>
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 pt-1">
        <div className="p-3.5 bg-slate-50 border border-border-subtle rounded-xl space-y-1">
          <span className="text-[11px] text-text-muted font-mono flex items-center gap-1.5">
            <HardDrive className="w-3.5 h-3.5 text-text-muted" /> Checkpoint Weight Path
          </span>
          <p className="text-xs font-mono text-text-primary truncate" title={model.weight_path}>
            {model.weight_path}
          </p>
        </div>

        <div className="p-3.5 bg-slate-50 border border-border-subtle rounded-xl space-y-1">
          <span className="text-[11px] text-text-muted font-mono flex items-center gap-1.5">
            <FileCheck className="w-3.5 h-3.5 text-text-muted" /> Checkpoint Status
          </span>
          <p className="text-xs font-mono font-bold text-emerald-700">
            {model.runtime_status}
          </p>
        </div>

        <div className="p-3.5 bg-slate-50 border border-border-subtle rounded-xl space-y-1">
          <span className="text-[11px] text-text-muted font-mono flex items-center gap-1.5">
            <Calendar className="w-3.5 h-3.5 text-text-muted" /> Registered Timestamp
          </span>
          <p className="text-xs font-mono text-text-primary">
            {model.trained_at ? new Date(model.trained_at).toLocaleString() : "Pre-trained Baseline"}
          </p>
        </div>

        <div className="p-3.5 bg-slate-50 border border-border-subtle rounded-xl space-y-1">
          <span className="text-[11px] text-text-muted font-mono flex items-center gap-1.5">
            <Cpu className="w-3.5 h-3.5 text-text-muted" /> Hardware Device
          </span>
          <p className="text-xs font-mono text-text-primary">
            {model.device || "cpu"}
          </p>
        </div>
      </div>

      <div className="pt-2">
        <span className="text-[11px] text-text-muted font-mono uppercase tracking-wider block mb-1.5">
          Supported Target Classes
        </span>
        <div className="flex flex-wrap gap-1.5">
          {model.supported_classes?.map((cls) => (
            <span
              key={cls}
              className="px-2.5 py-1 bg-bg-surface border border-border-subtle rounded-lg text-xs font-mono text-text-primary"
            >
              {cls}
            </span>
          ))}
          {model.unsupported_classes?.map((cls) => (
            <span
              key={cls}
              className="px-2.5 py-1 bg-slate-100 border border-slate-200 rounded-lg text-xs font-mono text-text-muted line-through"
              title="Not represented in benchmark or untrained"
            >
              {cls}
            </span>
          ))}
        </div>
      </div>
    </div>
  );
};
