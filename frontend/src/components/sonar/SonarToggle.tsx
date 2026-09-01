import React from "react";
import { Layers, Radio, CheckSquare, Square } from "lucide-react";
import { useAppStore } from "../../store/useAppStore";

export const SonarToggle: React.FC = () => {
  const {
    sonarMode,
    setSonarMode,
    sonarChannel,
    setSonarChannel,
    showDetections,
    setShowDetections,
    showSegmentation,
    setShowSegmentation,
    showClassification,
    setShowClassification,
    showConfidence,
    setShowConfidence,
    showGeolocation,
    setShowGeolocation,
  } = useAppStore();

  return (
    <div className="flex flex-wrap items-center justify-between gap-3 p-1.5 px-3 bg-bg-surface border border-border-subtle rounded-xl text-xs shadow-subtle">
      {/* Raw / Processed mode */}
      <div className="flex items-center gap-2">
        <span className="text-text-muted flex items-center gap-1 font-mono text-[11px]">
          <Layers className="w-3.5 h-3.5 text-accent" />
          Mode:
        </span>
        <div className="flex bg-slate-100 rounded-lg p-0.5 border border-border-subtle">
          <button
            type="button"
            onClick={() => setSonarMode("raw")}
            className={`px-2.5 py-1 rounded-md transition-all font-medium text-[11px] ${
              sonarMode === "raw"
                ? "bg-bg-surface text-text-primary font-bold shadow-sm"
                : "text-text-secondary hover:text-text-primary"
            }`}
          >
            Raw
          </button>
          <button
            type="button"
            onClick={() => setSonarMode("processed")}
            className={`px-2.5 py-1 rounded-md transition-all font-medium text-[11px] ${
              sonarMode === "processed"
                ? "bg-accent text-white font-bold shadow-sm"
                : "text-text-secondary hover:text-text-primary"
            }`}
          >
            Processed (CLAHE)
          </button>
        </div>
      </div>

      {/* Channel selector */}
      <div className="flex items-center gap-2">
        <span className="text-text-muted flex items-center gap-1 font-mono text-[11px]">
          <Radio className="w-3.5 h-3.5 text-sky-600" />
          Swath:
        </span>
        <div className="flex bg-slate-100 rounded-lg p-0.5 border border-border-subtle">
          <button
            type="button"
            onClick={() => setSonarChannel("starboard")}
            className={`px-2.5 py-1 rounded-md transition-all font-medium text-[11px] ${
              sonarChannel === "starboard"
                ? "bg-sky-600 text-white font-bold shadow-sm"
                : "text-text-secondary hover:text-text-primary"
            }`}
          >
            Starboard
          </button>
          <button
            type="button"
            onClick={() => setSonarChannel("port")}
            className={`px-2.5 py-1 rounded-md transition-all font-medium text-[11px] ${
              sonarChannel === "port"
                ? "bg-sky-600 text-white font-bold shadow-sm"
                : "text-text-secondary hover:text-text-primary"
            }`}
          >
            Port
          </button>
        </div>
      </div>

      {/* Layer Checkbox Controls */}
      <div className="flex flex-wrap items-center gap-3 border-l border-border-subtle pl-3 text-[11px] font-mono">
        <button
          type="button"
          onClick={() => setShowDetections(!showDetections)}
          className={`flex items-center gap-1.5 cursor-pointer ${
            showDetections ? "text-sky-700 font-bold" : "text-text-muted hover:text-text-secondary"
          }`}
        >
          {showDetections ? <CheckSquare className="w-3.5 h-3.5 text-sky-600" /> : <Square className="w-3.5 h-3.5" />}
          Detections
        </button>

        <button
          type="button"
          onClick={() => setShowSegmentation(!showSegmentation)}
          className={`flex items-center gap-1.5 cursor-pointer ${
            showSegmentation ? "text-purple-700 font-bold" : "text-text-muted hover:text-text-secondary"
          }`}
        >
          {showSegmentation ? <CheckSquare className="w-3.5 h-3.5 text-purple-600" /> : <Square className="w-3.5 h-3.5" />}
          Masks
        </button>

        <button
          type="button"
          onClick={() => setShowClassification(!showClassification)}
          className={`flex items-center gap-1.5 cursor-pointer ${
            showClassification ? "text-cyan-700 font-bold" : "text-text-muted hover:text-text-secondary"
          }`}
        >
          {showClassification ? <CheckSquare className="w-3.5 h-3.5 text-cyan-600" /> : <Square className="w-3.5 h-3.5" />}
          Classifier
        </button>

        <button
          type="button"
          onClick={() => setShowConfidence(!showConfidence)}
          className={`flex items-center gap-1.5 cursor-pointer ${
            showConfidence ? "text-emerald-700 font-bold" : "text-text-muted hover:text-text-secondary"
          }`}
        >
          {showConfidence ? <CheckSquare className="w-3.5 h-3.5 text-emerald-600" /> : <Square className="w-3.5 h-3.5" />}
          Confidence
        </button>

        <button
          type="button"
          onClick={() => setShowGeolocation(!showGeolocation)}
          className={`flex items-center gap-1.5 cursor-pointer ${
            showGeolocation ? "text-amber-800 font-bold" : "text-text-muted hover:text-text-secondary"
          }`}
        >
          {showGeolocation ? <CheckSquare className="w-3.5 h-3.5 text-amber-600" /> : <Square className="w-3.5 h-3.5" />}
          GPS Coordinates
        </button>
      </div>
    </div>
  );
};

export default SonarToggle;
