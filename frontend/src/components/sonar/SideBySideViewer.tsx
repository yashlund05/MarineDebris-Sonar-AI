import React from "react";
import { ShieldCheck, Sparkles, Hash } from "lucide-react";
import { DetectionBox } from "../../types/sonarEnhancement";

interface SideBySideViewerProps {
  rawImageUrl: string;
  enhancedImageUrl: string;
  enhancedGrayUrl: string;
  displayMode: "pseudocolor" | "grayscale";
  detections?: DetectionBox[] | null;
  showDetections?: boolean;
  rawSha256?: string;
  colormapName?: string;
}

export const SideBySideViewer: React.FC<SideBySideViewerProps> = ({
  rawImageUrl,
  enhancedImageUrl,
  enhancedGrayUrl,
  displayMode,
  detections,
  showDetections = false,
  rawSha256,
  colormapName = "Amber",
}) => {
  const activeEnhancedUrl = displayMode === "pseudocolor" ? enhancedImageUrl : enhancedGrayUrl;

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 w-full">
      {/* Left Pane: RAW SONAR */}
      <div className="rounded-2xl border border-border-subtle bg-bg-surface overflow-hidden shadow-sm flex flex-col">
        <div className="p-3 bg-bg-elevated/70 border-b border-border-subtle flex items-center justify-between text-xs">
          <div className="flex items-center gap-2 font-semibold text-text-primary">
            <ShieldCheck className="w-4 h-4 text-emerald-600" />
            <span>RAW SONAR (ORIGINAL)</span>
          </div>
          {rawSha256 && (
            <div className="flex items-center gap-1 font-mono text-[10px] text-text-muted bg-bg-surface px-2 py-0.5 rounded border border-border-subtle">
              <Hash className="w-3 h-3" />
              <span>{rawSha256.slice(0, 10)}...</span>
            </div>
          )}
        </div>
        <div className="relative w-full h-[420px] bg-black flex items-center justify-center p-2">
          <img
            src={rawImageUrl}
            alt="Raw Acoustic Sonar"
            className="w-full h-full object-contain"
          />
        </div>
        <div className="p-2.5 bg-bg-elevated/40 text-[11px] text-text-secondary border-t border-border-subtle flex justify-between">
          <span>Acoustic Backscatter</span>
          <span className="font-mono text-emerald-600 font-medium">100% Byte-Identical</span>
        </div>
      </div>

      {/* Right Pane: ENHANCED SONAR */}
      <div className="rounded-2xl border border-border-subtle bg-bg-surface overflow-hidden shadow-sm flex flex-col">
        <div className="p-3 bg-bg-elevated/70 border-b border-border-subtle flex items-center justify-between text-xs">
          <div className="flex items-center gap-2 font-semibold text-text-primary">
            <Sparkles className="w-4 h-4 text-accent" />
            <span>ENHANCED SONAR ({displayMode.toUpperCase()})</span>
          </div>
          <div className="text-[11px] font-mono text-accent font-medium bg-accent-subtle/50 px-2 py-0.5 rounded">
            {displayMode === "pseudocolor" ? colormapName : "Acoustic Grayscale"}
          </div>
        </div>
        <div className="relative w-full h-[420px] bg-black flex items-center justify-center p-2">
          <img
            src={activeEnhancedUrl}
            alt="Enhanced Acoustic Sonar"
            className="w-full h-full object-contain"
          />
          {/* Optional detections overlay */}
          {showDetections && detections && detections.length > 0 && (
            <div className="absolute inset-0 pointer-events-none p-2">
              {detections.map((d, i) => (
                <div
                  key={i}
                  className="absolute border-2 border-emerald-400 bg-emerald-500/10 rounded-sm"
                  style={{
                    left: `${Math.max(2, (d.bbox[0] / 640) * 100)}%`,
                    top: `${Math.max(2, (d.bbox[1] / 640) * 100)}%`,
                    width: `${Math.min(95, (d.bbox[2] / 640) * 100)}%`,
                    height: `${Math.min(95, (d.bbox[3] / 640) * 100)}%`,
                  }}
                >
                  <div className="absolute -top-6 left-0 bg-emerald-600 text-white text-[10px] font-mono px-1.5 py-0.5 rounded shadow whitespace-nowrap">
                    {d.class_name} ({(d.confidence * 100).toFixed(0)}%)
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
        <div className="p-2.5 bg-bg-elevated/40 text-[11px] text-text-secondary border-t border-border-subtle flex justify-between">
          <span>Radiometric Filtering</span>
          <span className="font-mono text-accent font-medium">SidescanTools Pipeline</span>
        </div>
      </div>
    </div>
  );
};
