import React from "react";
import { useQuery } from "@tanstack/react-query";
import { Cpu, CheckCircle2, Tag } from "lucide-react";
import { modelsApi } from "../api/models";
import { CLASS_COLORS } from "../utils/classColors";
import { DetectionClass, ModelRegistryItem } from "../types";

export const ModelsPage: React.FC = () => {
  const { data: modelsData, isLoading } = useQuery({
    queryKey: ["models"],
    queryFn: () => modelsApi.getModels(),
  });

  const models = modelsData?.data || [];

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-text-primary flex items-center gap-2">
          <Cpu className="w-6 h-6 text-accent" />
          Model Registry & Taxonomy Specification
        </h1>
        <p className="text-sm text-text-secondary mt-1">
          Registered acoustic object detectors, segmentation backbones, and target class definitions.
        </p>
      </div>

      {/* Baseline Active Model Spec */}
      <div className="bg-bg-surface border border-border-subtle rounded-2xl p-6 space-y-6 shadow-lg">
        <div className="flex flex-wrap items-center justify-between gap-4 border-b border-border-subtle pb-4">
          <div>
            <span className="text-xs font-mono font-semibold text-accent uppercase tracking-wider">
              Frozen Primary Detector Architecture
            </span>
            <h2 className="text-xl font-bold text-text-primary mt-1">
              sonar_yolov8m_ghostpot_v1 (v1.0.0)
            </h2>
          </div>
          <span className="inline-flex items-center gap-1.5 px-3 py-1 bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 rounded-full text-xs font-semibold">
            <CheckCircle2 className="w-3.5 h-3.5" />
            Active Deployment
          </span>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="p-4 bg-bg-elevated/40 border border-border-subtle rounded-xl">
            <span className="text-xs text-text-muted block">Detector Architecture</span>
            <span className="font-mono text-sm font-semibold text-text-primary mt-1 block">
              YOLOv8m
            </span>
          </div>
          <div className="p-4 bg-bg-elevated/40 border border-border-subtle rounded-xl">
            <span className="text-xs text-text-muted block">Tile Size & Overlap</span>
            <span className="font-mono text-sm font-semibold text-text-primary mt-1 block">
              640×640 px (20% overlap)
            </span>
          </div>
          <div className="p-4 bg-bg-elevated/40 border border-border-subtle rounded-xl">
            <span className="text-xs text-text-muted block">Default Confidence</span>
            <span className="font-mono text-sm font-semibold text-text-primary mt-1 block">
              0.35 (NMS IoU: 0.45)
            </span>
          </div>
          <div className="p-4 bg-bg-elevated/40 border border-border-subtle rounded-xl">
            <span className="text-xs text-text-muted block">Calibration Scaler</span>
            <span className="font-mono text-sm font-semibold text-text-primary mt-1 block">
              Platt / Temperature (1.4)
            </span>
          </div>
        </div>
      </div>

      {/* Target Debris Taxonomy */}
      <div className="bg-bg-surface border border-border-subtle rounded-2xl p-6 space-y-4 shadow-lg">
        <div className="flex items-center gap-2">
          <Tag className="w-5 h-5 text-accent" />
          <h3 className="text-base font-semibold text-text-primary">
            Canonical Marine Debris Taxonomy (SIH PS26057)
          </h3>
        </div>
        <p className="text-xs text-text-secondary">
          Frozen 5-class target taxonomy plus natural feature audit class.
        </p>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3 pt-2">
          {(Object.keys(CLASS_COLORS) as DetectionClass[]).map((cls) => {
            const meta = CLASS_COLORS[cls];
            return (
              <div
                key={cls}
                className="p-4 rounded-xl border flex items-center gap-3.5 transition-all"
                style={{
                  backgroundColor: meta.bg,
                  borderColor: `${meta.border}50`,
                }}
              >
                <div
                  className="w-4 h-4 rounded-full flex-shrink-0 shadow-sm"
                  style={{ backgroundColor: meta.color }}
                />
                <div>
                  <p className="text-xs font-bold" style={{ color: meta.text }}>
                    {meta.label}
                  </p>
                  <p className="text-[10px] font-mono text-text-muted mt-0.5">
                    {cls}
                  </p>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Model Registry Database Entries */}
      <div className="bg-bg-surface border border-border-subtle rounded-2xl p-6 space-y-4 shadow-lg">
        <h3 className="text-base font-semibold text-text-primary">
          Model Registry Index
        </h3>

        {isLoading ? (
          <p className="text-xs text-text-muted">Loading registry entries...</p>
        ) : models.length === 0 ? (
          <div className="p-4 bg-bg-elevated/40 border border-border-subtle rounded-xl text-xs text-text-muted space-y-1">
            <p className="font-semibold text-text-secondary">No additional custom models registered</p>
            <p>
              Baseline detector weights are loaded from configured path (<code className="text-text-primary">models/detection/sonar_yolov8m_ghostpot_v1.pt</code>).
            </p>
          </div>
        ) : (
          <div className="space-y-3">
            {models.map((m: ModelRegistryItem) => (
              <div
                key={m.id}
                className="p-4 bg-bg-elevated/50 border border-border-subtle rounded-xl flex items-center justify-between text-xs"
              >
                <div>
                  <h4 className="font-semibold text-text-primary">{m.model_name}</h4>
                  <p className="text-text-muted font-mono">v{m.version} • {m.task}</p>
                </div>
                {m.is_active && (
                  <span className="px-2.5 py-0.5 bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 rounded-full font-medium">
                    Active
                  </span>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default ModelsPage;
