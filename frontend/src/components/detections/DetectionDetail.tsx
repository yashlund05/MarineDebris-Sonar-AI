import React from "react";
import {
  X,
  MapPin,
  Ruler,
  Target,
  ShieldCheck,
  ShieldAlert,
  Layers,
  CheckCircle2,
  AlertCircle,
  Sparkles,
} from "lucide-react";
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

  const seg = selectedDetection.segmentation;
  const isSegAvailable = seg?.status === "available";

  const classif = selectedDetection.classification;
  const isClassifAvailable = classif?.status === "available";

  return (
    <div className="fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center p-4">
      <div className="bg-bg-surface border border-border-subtle rounded-2xl w-full max-w-2xl shadow-modal overflow-hidden animate-in fade-in duration-150">
        {/* Inspection Header */}
        <div className="p-4 px-6 border-b border-border-subtle flex items-center justify-between bg-slate-50/70">
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
            className="p-1.5 text-text-muted hover:text-text-primary rounded-lg hover:bg-slate-200/60 transition-all cursor-pointer"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Modal Body */}
        <div className="p-6 space-y-4 max-h-[75vh] overflow-y-auto">
          {/* Metadata Bar */}
          <div className="grid grid-cols-2 gap-4 p-3.5 bg-slate-50 border border-border-subtle rounded-xl font-mono text-xs">
            <div>
              <span className="text-text-muted block text-[10px] uppercase tracking-wider mb-0.5">
                Detection Code
              </span>
              <span className="text-text-primary font-bold text-sm">
                {selectedDetection.detection_code}
              </span>
            </div>
            <div>
              <span className="text-text-muted block text-[10px] uppercase tracking-wider mb-0.5">
                Target UUID
              </span>
              <span className="text-text-secondary truncate block font-mono text-xs">
                {selectedDetection.id}
              </span>
            </div>
          </div>

          {/* Secondary Classification Panel */}
          <div className="p-4 bg-bg-surface border border-border-subtle rounded-xl space-y-2.5 shadow-subtle">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2 text-xs font-bold text-text-primary">
                <Sparkles className="w-4 h-4 text-sky-600" />
                Secondary Classification Verification (MobileNet)
              </div>
              <span
                className={`px-2.5 py-0.5 rounded-full text-[10px] font-mono font-semibold uppercase ${
                  isClassifAvailable
                    ? "bg-sky-50 text-sky-800 border border-sky-200"
                    : "bg-slate-100 text-slate-600 border border-slate-200"
                }`}
              >
                {isClassifAvailable ? "AVAILABLE" : "CLASSIFIER UNAVAILABLE"}
              </span>
            </div>

            {isClassifAvailable ? (
              <div className="space-y-2 pt-1 font-mono text-xs">
                <div className="flex justify-between p-2 bg-slate-50 rounded-lg">
                  <span className="text-text-secondary">Classifier Model:</span>
                  <span className="text-text-primary font-semibold">{classif?.model || "MobileNet"}</span>
                </div>
                <div className="flex justify-between p-2 bg-slate-50 rounded-lg">
                  <span className="text-text-secondary">Predicted Crop Class:</span>
                  <span className="text-sky-700 font-semibold">{classif?.class_name || "N/A"}</span>
                </div>
                <div className="flex justify-between p-2 bg-slate-50 rounded-lg">
                  <span className="text-text-secondary">Consensus Agreement:</span>
                  <span
                    className={`font-semibold flex items-center gap-1 ${
                      classif?.agreement ? "text-emerald-700" : "text-amber-800"
                    }`}
                  >
                    {classif?.agreement ? (
                      <>
                        <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" /> AGREED (High Consensus)
                      </>
                    ) : (
                      <>
                        <AlertCircle className="w-3.5 h-3.5 text-amber-600" /> REVIEW (Disagreement)
                      </>
                    )}
                  </span>
                </div>
              </div>
            ) : (
              <p className="text-[11px] text-text-muted italic pt-0.5">
                Secondary classification checkpoint not loaded. YOLOv8m detection accepted as single source of truth.
              </p>
            )}
          </div>

          {/* Segmentation Mask Panel */}
          <div className="p-4 bg-bg-surface border border-border-subtle rounded-xl space-y-2.5 shadow-subtle">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2 text-xs font-bold text-text-primary">
                <Layers className="w-4 h-4 text-purple-600" />
                Semantic Segmentation (U-Net / SegFormer)
              </div>
              <span
                className={`px-2.5 py-0.5 rounded-full text-[10px] font-mono font-semibold uppercase ${
                  isSegAvailable
                    ? "bg-purple-50 text-purple-800 border border-purple-200"
                    : "bg-slate-100 text-slate-600 border border-slate-200"
                }`}
              >
                {isSegAvailable ? "AVAILABLE" : "SEGMENTATION UNAVAILABLE"}
              </span>
            </div>

            {isSegAvailable ? (
              <div className="grid grid-cols-3 gap-2 font-mono text-xs pt-1">
                <div className="p-2 bg-slate-50 rounded-lg">
                  <span className="text-[10px] text-text-muted block">Confidence</span>
                  <span className="font-semibold text-purple-700">
                    {seg?.confidence ? `${(seg.confidence * 100).toFixed(1)}%` : "N/A"}
                  </span>
                </div>
                <div className="p-2 bg-slate-50 rounded-lg">
                  <span className="text-[10px] text-text-muted block">Mask Area</span>
                  <span className="font-semibold text-text-primary">
                    {seg?.mask_area ? `${seg.mask_area} px²` : "N/A"}
                  </span>
                </div>
                <div className="p-2 bg-slate-50 rounded-lg">
                  <span className="text-[10px] text-text-muted block">Geometry Format</span>
                  <span className="font-semibold text-text-secondary">RLE / Contour</span>
                </div>
              </div>
            ) : (
              <p className="text-[11px] text-text-muted italic pt-0.5">
                Acoustic segmentation model checkpoint not deployed on this instance. Detector bounding box serves as authoritative boundary.
              </p>
            )}
          </div>

          {/* Metric Dimensions & Coordinates */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Georeferencing */}
            <div className="p-4 bg-bg-surface border border-border-subtle rounded-xl space-y-2.5 shadow-subtle">
              <div className="flex items-center gap-2 text-xs font-bold text-sky-700">
                <MapPin className="w-4 h-4" />
                Geographic Coordinates (WGS84)
              </div>
              {selectedDetection.geotagging_available &&
              selectedDetection.latitude !== undefined &&
              selectedDetection.latitude !== null &&
              selectedDetection.longitude !== undefined &&
              selectedDetection.longitude !== null ? (
                <div className="font-mono text-xs space-y-1.5 pt-1">
                  <div className="flex justify-between">
                    <span className="text-text-secondary">Latitude:</span>
                    <span className="text-text-primary font-bold">
                      {selectedDetection.latitude.toFixed(6)}°
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-text-secondary">Longitude:</span>
                    <span className="text-text-primary font-bold">
                      {selectedDetection.longitude.toFixed(6)}°
                    </span>
                  </div>
                </div>
              ) : (
                <p className="text-xs text-text-muted italic pt-1">
                  Location unavailable — navigation metadata was absent from source ping record.
                </p>
              )}
            </div>

            {/* Estimated Dimensions */}
            <div className="p-4 bg-bg-surface border border-border-subtle rounded-xl space-y-2.5 shadow-subtle">
              <div className="flex items-center gap-2 text-xs font-bold text-amber-800">
                <Ruler className="w-4 h-4" />
                Physical Metric Dimensions
              </div>
              <div className="font-mono text-xs space-y-1.5 pt-1">
                <div className="flex justify-between">
                  <span className="text-text-secondary">Est. Length:</span>
                  <span className="text-text-primary font-bold">
                    {selectedDetection.estimated_length_m !== undefined &&
                    selectedDetection.estimated_length_m !== null
                      ? `${selectedDetection.estimated_length_m.toFixed(2)} m`
                      : "N/A"}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-text-secondary">Est. Width:</span>
                  <span className="text-text-primary font-bold">
                    {selectedDetection.estimated_width_m !== undefined &&
                    selectedDetection.estimated_width_m !== null
                      ? `${selectedDetection.estimated_width_m.toFixed(2)} m`
                      : "N/A"}
                  </span>
                </div>
              </div>
            </div>
          </div>

          {/* Swath Pixel Coordinates */}
          <div className="p-4 bg-slate-50 border border-border-subtle rounded-xl space-y-2">
            <div className="flex items-center gap-2 text-xs font-bold text-text-primary">
              <Target className="w-4 h-4 text-accent" />
              Swath Pixel Coordinates
            </div>
            <div className="grid grid-cols-4 gap-2 font-mono text-xs text-center">
              <div className="p-2 bg-bg-surface border border-border-subtle rounded-lg">
                <span className="text-text-muted text-[10px] block">X</span>
                <span className="font-bold text-text-primary">{selectedDetection.bbox_x}</span>
              </div>
              <div className="p-2 bg-bg-surface border border-border-subtle rounded-lg">
                <span className="text-text-muted text-[10px] block">Y</span>
                <span className="font-bold text-text-primary">{selectedDetection.bbox_y}</span>
              </div>
              <div className="p-2 bg-bg-surface border border-border-subtle rounded-lg">
                <span className="text-text-muted text-[10px] block">Width</span>
                <span className="font-bold text-text-primary">{selectedDetection.bbox_w}</span>
              </div>
              <div className="p-2 bg-bg-surface border border-border-subtle rounded-lg">
                <span className="text-text-muted text-[10px] block">Height</span>
                <span className="font-bold text-text-primary">{selectedDetection.bbox_h}</span>
              </div>
            </div>
          </div>

          {/* False-Positive / Filter Audit */}
          {selectedDetection.is_filtered ? (
            <div className="p-3.5 bg-rose-50 border border-rose-200 rounded-xl text-rose-800 text-xs flex items-center gap-3">
              <ShieldAlert className="w-5 h-5 flex-shrink-0 text-rose-600" />
              <div>
                <p className="font-bold">Flagged as False Positive / Artifact</p>
                <p className="text-rose-700 mt-0.5">
                  Reason: {selectedDetection.filtered_reason || "Size / Shadow anomaly"}
                </p>
              </div>
            </div>
          ) : (
            <div className="p-3 bg-emerald-50 border border-emerald-200 rounded-xl text-emerald-800 text-xs flex items-center gap-2.5">
              <ShieldCheck className="w-4 h-4 flex-shrink-0 text-emerald-600" />
              <span>Verified target passing acoustic shadow and geometry constraints</span>
            </div>
          )}
        </div>

        {/* Modal Footer */}
        <div className="p-4 px-6 border-t border-border-subtle bg-slate-50/70 flex justify-end">
          <button
            type="button"
            onClick={close}
            className="px-5 py-2 bg-bg-surface hover:bg-slate-100 border border-border-default text-text-primary text-xs font-semibold rounded-xl transition-all cursor-pointer shadow-subtle"
          >
            Close Inspection
          </button>
        </div>
      </div>
    </div>
  );
};

export default DetectionDetail;
