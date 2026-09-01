import React from "react";
import { Layers, Eye, EyeOff, Radio } from "lucide-react";
import { useAppStore } from "../../store/useAppStore";

export const SonarToggle: React.FC = () => {
  const {
    sonarMode,
    setSonarMode,
    sonarChannel,
    setSonarChannel,
    showOverlay,
    setShowOverlay,
  } = useAppStore();

  return (
    <div className="flex flex-wrap items-center justify-between gap-3 p-2.5 px-4 bg-bg-surface/90 backdrop-blur border border-border-subtle rounded-xl text-xs">
      {/* Raw / Processed mode */}
      <div className="flex items-center gap-2">
        <span className="text-text-secondary flex items-center gap-1">
          <Layers className="w-3.5 h-3.5 text-accent" />
          Mode:
        </span>
        <div className="flex bg-bg-elevated rounded-lg p-0.5">
          <button
            type="button"
            onClick={() => setSonarMode("raw")}
            className={`px-2.5 py-1 rounded-md transition-all font-medium ${
              sonarMode === "raw"
                ? "bg-accent text-white font-semibold shadow-sm"
                : "text-text-secondary hover:text-text-primary"
            }`}
          >
            Raw
          </button>
          <button
            type="button"
            onClick={() => setSonarMode("processed")}
            className={`px-2.5 py-1 rounded-md transition-all font-medium ${
              sonarMode === "processed"
                ? "bg-accent text-white font-semibold shadow-sm"
                : "text-text-secondary hover:text-text-primary"
            }`}
          >
            Processed (CLAHE)
          </button>
        </div>
      </div>

      {/* Channel selector */}
      <div className="flex items-center gap-2">
        <span className="text-text-secondary flex items-center gap-1">
          <Radio className="w-3.5 h-3.5 text-cyan-400" />
          Swath:
        </span>
        <div className="flex bg-bg-elevated rounded-lg p-0.5">
          <button
            type="button"
            onClick={() => setSonarChannel("starboard")}
            className={`px-2.5 py-1 rounded-md transition-all font-medium ${
              sonarChannel === "starboard"
                ? "bg-cyan-600 text-white font-semibold"
                : "text-text-secondary hover:text-text-primary"
            }`}
          >
            Starboard
          </button>
          <button
            type="button"
            onClick={() => setSonarChannel("port")}
            className={`px-2.5 py-1 rounded-md transition-all font-medium ${
              sonarChannel === "port"
                ? "bg-cyan-600 text-white font-semibold"
                : "text-text-secondary hover:text-text-primary"
            }`}
          >
            Port
          </button>
        </div>
      </div>

      {/* Overlay Toggle */}
      <button
        type="button"
        onClick={() => setShowOverlay(!showOverlay)}
        className={`flex items-center gap-1.5 px-3 py-1 rounded-lg border font-medium transition-all ${
          showOverlay
            ? "border-accent/40 bg-accent/10 text-accent font-semibold"
            : "border-border-subtle text-text-muted hover:text-text-secondary"
        }`}
      >
        {showOverlay ? <Eye className="w-3.5 h-3.5" /> : <EyeOff className="w-3.5 h-3.5" />}
        Detections Overlay
      </button>
    </div>
  );
};
