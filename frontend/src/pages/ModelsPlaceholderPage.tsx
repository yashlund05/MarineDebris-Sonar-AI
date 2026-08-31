import React from "react";

export const ModelsPlaceholderPage: React.FC = () => {
  return (
    <div className="space-y-6">
      <div className="border-b border-border-subtle pb-4">
        <h1 className="text-2xl font-bold text-text-primary tracking-tight">
          Model Registry & Versioning
        </h1>
        <p className="text-sm text-text-secondary mt-1">
          Active detection, segmentation, and edge optimization models conforming to DB_SCHEMA.md.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="bg-bg-surface border border-border-subtle rounded-lg p-5 space-y-3">
          <div className="flex items-center justify-between">
            <span className="font-semibold text-text-primary text-sm">Baseline Detection Model</span>
            <span className="text-xs px-2 py-0.5 rounded bg-emerald-950/60 text-emerald-400 border border-emerald-800 font-mono">
              SPEC DEFINED
            </span>
          </div>
          <div className="space-y-1.5 text-xs text-text-secondary">
            <div className="flex justify-between">
              <span>Architecture:</span>
              <span className="font-mono text-text-primary">YOLOv8m (Ultralytics)</span>
            </div>
            <div className="flex justify-between">
              <span>Model Identifier:</span>
              <span className="font-mono text-text-primary">sonar_yolov8m_ghostpot_v1</span>
            </div>
            <div className="flex justify-between">
              <span>Version:</span>
              <span className="font-mono text-text-primary">1.0.0</span>
            </div>
            <div className="flex justify-between">
              <span>Input Resolution:</span>
              <span className="font-mono text-text-primary">640×640 tiles (0.2 overlap)</span>
            </div>
          </div>
        </div>

        <div className="bg-bg-surface border border-border-subtle rounded-lg p-5 space-y-3">
          <div className="flex items-center justify-between">
            <span className="font-semibold text-text-primary text-sm">Target Debris Taxonomy</span>
            <span className="text-xs px-2 py-0.5 rounded bg-blue-950/60 text-accent border border-accent/30 font-mono">
              6 CLASSES
            </span>
          </div>
          <ul className="text-xs space-y-1 text-text-secondary font-mono">
            <li className="flex items-center space-x-2">
              <span className="w-2 h-2 rounded-full bg-detection-gear" />
              <span>derelict_fishing_gear</span>
            </li>
            <li className="flex items-center space-x-2">
              <span className="w-2 h-2 rounded-full bg-detection-debris" />
              <span>general_marine_debris</span>
            </li>
            <li className="flex items-center space-x-2">
              <span className="w-2 h-2 rounded-full bg-detection-wreck" />
              <span>shipwreck</span>
            </li>
            <li className="flex items-center space-x-2">
              <span className="w-2 h-2 rounded-full bg-detection-pipe" />
              <span>pipe_or_cylinder</span>
            </li>
            <li className="flex items-center space-x-2">
              <span className="w-2 h-2 rounded-full bg-detection-other" />
              <span>other_man_made_target</span>
            </li>
            <li className="flex items-center space-x-2">
              <span className="w-2 h-2 rounded-full bg-detection-natural" />
              <span>natural_feature (audit only)</span>
            </li>
          </ul>
        </div>
      </div>
    </div>
  );
};
