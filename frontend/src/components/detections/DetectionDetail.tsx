import React from "react";
import { X, MapPin, Ruler, Target, Hash, Clock, ShieldCheck, ShieldAlert } from "lucide-react";
import { useAppStore } from "../../store/useAppStore";
import { ClassBadge } from "../ui/ClassBadge";
import { ConfidenceBadge } from "../ui/ConfidenceBadge";

export const DetectionDetail: React.FC = () => {
  const {
    selectedDetection,
    setSelectedDetection,
    isDetectionModalOpen,
    setDetectionModalOpen,
  } = useAppStore();

  if (!isDetectionModalOpen || !selectedDetection) return null;

  const close = () => {
    setDetectionModalOpen(false);
    setSelectedDetection(null);
  };

  return (
    <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="bg-bg-surface border border-border-subtle rounded-2xl w-full max-w-xl shadow-2xl overflow-hidden animate-in fade-in duration-200">
        {/* Modal Header */}
        <div className="p-4 px-6 border-b border-border-subtle flex items-center justify-between bg-bg-elevated/40">
          <div className="flex items-center gap-3">
            <ClassBadge className={selectedDetection.class_name} size="md" />
            <ConfidenceBadge
              confidence={selectedDetection.confidence}
              calibrated={selectedDetection.confidence_calibrated}
            />
          </div>
          <button
            type="button"
            onClick={close}
            className="p-1.5 text-text-secondary hover:text-text-primary rounded-lg hover:bg-bg-surface transition-all cursor-pointer"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Modal Body */}
        <div className="p-6 space-y-6 max-h-[75vh] overflow-y-auto">
          {/* Identification & Codes */}
          <div className="grid grid-cols-2 gap-4 p-4 bg-bg-elevated/50 rounded-xl font-mono text-xs">
            <div>
              <span className="text-text-muted block text-[11px] uppercase tracking-wider mb-1">
                Detection Code
              </span>
              <span className="text-text-primary font-semibold text-sm">
                {selectedDetection.detection_code}
              </span>
            </div>
            <div>
              <span className="text-text-muted block text-[11px] uppercase tracking-wider mb-1">
                Detection UUID
              </span>
              <span className="text-text-secondary truncate block">
                {selectedDetection.id}
              </span>
            </div>
          </div>

          {/* Metric Dimensions & Coordinates */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Georeferencing */}
            <div className="p-4 bg-bg-elevated/40 border border-border-subtle rounded-xl space-y-3">
              <div className="flex items-center gap-2 text-xs font-semibold text-cyan-400">
                <MapPin className="w-4 h-4" />
                Geographic Coordinates (WGS84)
              </div>
              {selectedDetection.geotagging_available &&
              selectedDetection.latitude !== undefined &&
              selectedDetection.latitude !== null &&
              selectedDetection.longitude !== undefined &&
              selectedDetection.longitude !== null ? (
                <div className="font-mono text-xs space-y-1.5">
                  <div className="flex justify-between">
                    <span className="text-text-secondary">Latitude:</span>
                    <span className="text-text-primary font-semibold">
                      {selectedDetection.latitude.toFixed(6)}°
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-text-secondary">Longitude:</span>
                    <span className="text-text-primary font-semibold">
                      {selectedDetection.longitude.toFixed(6)}°
                    </span>
                  </div>
                </div>
              ) : (
                <p className="text-xs text-text-muted italic">
                  Location unavailable — navigation metadata was absent from source ping record.
                </p>
              )}
            </div>

            {/* Estimated Dimensions */}
            <div className="p-4 bg-bg-elevated/40 border border-border-subtle rounded-xl space-y-3">
              <div className="flex items-center gap-2 text-xs font-semibold text-amber-400">
                <Ruler className="w-4 h-4" />
                Physical Dimensions
              </div>
              <div className="font-mono text-xs space-y-1.5">
                <div className="flex justify-between">
                  <span className="text-text-secondary">Est. Length:</span>
                  <span className="text-text-primary font-semibold">
                    {selectedDetection.estimated_length_m !== undefined &&
                    selectedDetection.estimated_length_m !== null
                      ? `${selectedDetection.estimated_length_m.toFixed(2)} m`
                      : "N/A"}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-text-secondary">Est. Width:</span>
                  <span className="text-text-primary font-semibold">
                    {selectedDetection.estimated_width_m !== undefined &&
                    selectedDetection.estimated_width_m !== null
                      ? `${selectedDetection.estimated_width_m.toFixed(2)} m`
                      : "N/A"}
                  </span>
                </div>
              </div>
            </div>
          </div>

          {/* Sonar Image Bounding Box */}
          <div className="p-4 bg-bg-elevated/40 border border-border-subtle rounded-xl space-y-3">
            <div className="flex items-center gap-2 text-xs font-semibold text-text-primary">
              <Target className="w-4 h-4 text-accent" />
              Swath Pixel Coordinates
            </div>
            <div className="grid grid-cols-4 gap-2 font-mono text-xs text-center">
              <div className="p-2 bg-bg-surface rounded-lg">
                <span className="text-text-muted text-[10px] block">X</span>
                <span className="font-semibold text-text-primary">{selectedDetection.bbox_x}</span>
              </div>
              <div className="p-2 bg-bg-surface rounded-lg">
                <span className="text-text-muted text-[10px] block">Y</span>
                <span className="font-semibold text-text-primary">{selectedDetection.bbox_y}</span>
              </div>
              <div className="p-2 bg-bg-surface rounded-lg">
                <span className="text-text-muted text-[10px] block">Width</span>
                <span className="font-semibold text-text-primary">{selectedDetection.bbox_w}</span>
              </div>
              <div className="p-2 bg-bg-surface rounded-lg">
                <span className="text-text-muted text-[10px] block">Height</span>
                <span className="font-semibold text-text-primary">{selectedDetection.bbox_h}</span>
              </div>
            </div>
          </div>

          {/* Ping and Filter Context */}
          <div className="grid grid-cols-2 gap-4 font-mono text-xs">
            <div className="flex items-center gap-2 text-text-secondary">
              <Hash className="w-4 h-4 text-text-muted" />
              <span>Ping: {selectedDetection.ping_number ?? "N/A"}</span>
            </div>
            <div className="flex items-center gap-2 text-text-secondary">
              <Clock className="w-4 h-4 text-text-muted" />
              <span>
                Timestamp:{" "}
                {selectedDetection.ping_timestamp
                  ? `${selectedDetection.ping_timestamp.toFixed(2)}s`
                  : "N/A"}
              </span>
            </div>
          </div>

          {/* False-Positive / Filter Audit */}
          {selectedDetection.is_filtered ? (
            <div className="p-3.5 bg-red-950/40 border border-red-500/30 rounded-xl text-red-400 text-xs flex items-center gap-3">
              <ShieldAlert className="w-5 h-5 flex-shrink-0" />
              <div>
                <p className="font-semibold">Flagged as False Positive / Artifact</p>
                <p className="text-red-300/80 mt-0.5">
                  Reason: {selectedDetection.filtered_reason || "Size / Shadow anomaly"}
                </p>
              </div>
            </div>
          ) : (
            <div className="p-3 bg-emerald-950/30 border border-emerald-500/20 rounded-xl text-emerald-400 text-xs flex items-center gap-2.5">
              <ShieldCheck className="w-4 h-4 flex-shrink-0" />
              <span>Verified target passing acoustic shadow and geometry constraints</span>
            </div>
          )}
        </div>

        {/* Modal Footer */}
        <div className="p-4 px-6 border-t border-border-subtle bg-bg-elevated/40 flex justify-end">
          <button
            type="button"
            onClick={close}
            className="px-5 py-2 bg-bg-elevated hover:bg-bg-surface border border-border-subtle text-text-primary text-xs font-semibold rounded-xl transition-all cursor-pointer"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
};
