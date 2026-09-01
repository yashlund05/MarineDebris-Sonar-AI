import React from "react";
import { Detection } from "../../types";
import { ClassBadge } from "../ui/ClassBadge";
import { ConfidenceBadge } from "../ui/ConfidenceBadge";
import { MapPin, Ruler, AlertTriangle } from "lucide-react";
import { useAppStore } from "../../store/useAppStore";

interface DetectionCardProps {
  detection: Detection;
}

export const DetectionCard: React.FC<DetectionCardProps> = ({ detection }) => {
  const { selectedDetection, setSelectedDetection } = useAppStore();
  const isSelected = selectedDetection?.id === detection.id;

  return (
    <div
      onClick={() => setSelectedDetection(detection)}
      className={`p-3.5 rounded-xl border transition-all cursor-pointer space-y-2 ${
        isSelected
          ? "bg-accent/10 border-accent shadow-md ring-1 ring-accent/50"
          : "bg-bg-surface border-border-subtle hover:border-accent/40 hover:bg-bg-elevated/40"
      }`}
    >
      <div className="flex items-start justify-between gap-2">
        <ClassBadge className={detection.class_name} size="sm" />
        <ConfidenceBadge
          confidence={detection.confidence}
          calibrated={detection.confidence_calibrated}
        />
      </div>

      <div className="grid grid-cols-2 gap-2 text-xs font-mono text-text-secondary pt-1">
        <div className="flex items-center gap-1.5">
          <MapPin className="w-3.5 h-3.5 text-cyan-400 flex-shrink-0" />
          {detection.geotagging_available &&
          detection.latitude !== undefined &&
          detection.latitude !== null &&
          detection.longitude !== undefined &&
          detection.longitude !== null ? (
            <span className="truncate">
              {detection.latitude.toFixed(4)}, {detection.longitude.toFixed(4)}
            </span>
          ) : (
            <span className="text-text-muted italic">No GPS</span>
          )}
        </div>

        <div className="flex items-center gap-1.5 justify-end">
          <Ruler className="w-3.5 h-3.5 text-amber-400 flex-shrink-0" />
          {detection.estimated_length_m !== undefined && detection.estimated_length_m !== null ? (
            <span>
              {detection.estimated_length_m.toFixed(1)}m × {detection.estimated_width_m?.toFixed(1) || "?"}m
            </span>
          ) : (
            <span className="text-text-muted">
              {detection.bbox_w}×{detection.bbox_h} px
            </span>
          )}
        </div>
      </div>

      {detection.is_filtered && (
        <div className="flex items-center gap-1.5 text-[11px] text-red-400 bg-red-950/30 px-2 py-0.5 rounded border border-red-500/20">
          <AlertTriangle className="w-3 h-3 flex-shrink-0" />
          <span className="truncate">Filtered: {detection.filtered_reason || "Anomaly"}</span>
        </div>
      )}
    </div>
  );
};
