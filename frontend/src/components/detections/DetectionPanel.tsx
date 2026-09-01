import React from "react";
import { Detection } from "../../types";
import { DetectionCard } from "./DetectionCard";
import { useAppStore } from "../../store/useAppStore";
import { Target, SearchX } from "lucide-react";

interface DetectionPanelProps {
  detections: Detection[];
}

export const DetectionPanel: React.FC<DetectionPanelProps> = ({ detections }) => {
  const { selectedClass, minConfidence, includeFiltered } = useAppStore();

  const filteredDetections = detections.filter((d) => {
    if (selectedClass !== "all" && d.class_name !== selectedClass) return false;
    if (d.confidence < minConfidence) return false;
    if (!includeFiltered && d.is_filtered) return false;
    return true;
  });

  return (
    <div className="flex flex-col h-full bg-bg-surface border border-border-subtle rounded-2xl overflow-hidden shadow-lg">
      {/* Header */}
      <div className="p-4 border-b border-border-subtle flex items-center justify-between bg-bg-surface">
        <div className="flex items-center gap-2">
          <Target className="w-4 h-4 text-accent" />
          <h3 className="text-sm font-semibold text-text-primary">Detected Targets</h3>
        </div>
        <span className="px-2.5 py-0.5 rounded-full bg-bg-elevated text-xs font-mono font-medium text-text-secondary">
          {filteredDetections.length} of {detections.length}
        </span>
      </div>

      {/* Detections List */}
      <div className="flex-1 overflow-y-auto p-4 space-y-3">
        {filteredDetections.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-48 text-center p-4 text-text-muted space-y-2">
            <SearchX className="w-8 h-8 stroke-1 text-text-muted" />
            <p className="text-sm font-medium text-text-secondary">No detections matching filters</p>
            <p className="text-xs max-w-xs">
              Adjust minimum confidence or toggle filtered anomalies to inspect targets.
            </p>
          </div>
        ) : (
          filteredDetections.map((det) => (
            <DetectionCard key={det.id} detection={det} />
          ))
        )}
      </div>
    </div>
  );
};
