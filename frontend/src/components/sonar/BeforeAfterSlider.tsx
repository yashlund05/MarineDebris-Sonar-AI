import React, { useState, useRef, useCallback, useEffect } from "react";
import { MoveHorizontal, Eye, ShieldCheck } from "lucide-react";
import { DetectionBox } from "../../types/sonarEnhancement";

interface BeforeAfterSliderProps {
  rawImageUrl: string;
  enhancedImageUrl: string;
  enhancedGrayUrl: string;
  displayMode: "pseudocolor" | "grayscale";
  detections?: DetectionBox[] | null;
  showDetections?: boolean;
  rawSha256?: string;
  colormapName?: string;
}

export const BeforeAfterSlider: React.FC<BeforeAfterSliderProps> = ({
  rawImageUrl,
  enhancedImageUrl,
  enhancedGrayUrl,
  displayMode,
  detections,
  showDetections = false,
  rawSha256,
  colormapName = "Amber",
}) => {
  const [sliderPosition, setSliderPosition] = useState<number>(50); // percentage (0 - 100)
  const [isDragging, setIsDragging] = useState<boolean>(false);
  const containerRef = useRef<HTMLDivElement>(null);

  const activeEnhancedUrl = displayMode === "pseudocolor" ? enhancedImageUrl : enhancedGrayUrl;

  const handleMove = useCallback((clientX: number) => {
    if (!containerRef.current) return;
    const rect = containerRef.current.getBoundingClientRect();
    const x = clientX - rect.left;
    const percentage = Math.max(0, Math.min(100, (x / rect.width) * 100));
    setSliderPosition(percentage);
  }, []);

  const handleMouseDown = useCallback((e: React.MouseEvent) => {
    e.preventDefault();
    setIsDragging(true);
    handleMove(e.clientX);
  }, [handleMove]);

  const handleTouchStart = useCallback((e: React.TouchEvent) => {
    setIsDragging(true);
    if (e.touches.length > 0) {
      handleMove(e.touches[0].clientX);
    }
  }, [handleMove]);

  useEffect(() => {
    const handleMouseUp = () => setIsDragging(false);
    const handleMouseMove = (e: MouseEvent) => {
      if (isDragging) handleMove(e.clientX);
    };
    const handleTouchMove = (e: TouchEvent) => {
      if (isDragging && e.touches.length > 0) handleMove(e.touches[0].clientX);
    };

    if (isDragging) {
      window.addEventListener("mousemove", handleMouseMove);
      window.addEventListener("mouseup", handleMouseUp);
      window.addEventListener("touchmove", handleTouchMove);
      window.addEventListener("touchend", handleMouseUp);
    }
    return () => {
      window.removeEventListener("mousemove", handleMouseMove);
      window.removeEventListener("mouseup", handleMouseUp);
      window.removeEventListener("touchmove", handleTouchMove);
      window.removeEventListener("touchend", handleMouseUp);
    };
  }, [isDragging, handleMove]);

  return (
    <div className="relative w-full rounded-2xl overflow-hidden border border-border-subtle bg-black shadow-lg select-none">
      {/* Container with aspect ratio preservation */}
      <div
        ref={containerRef}
        className="relative w-full h-[520px] cursor-ew-resize overflow-hidden flex items-center justify-center bg-black/90"
        onMouseDown={handleMouseDown}
        onTouchStart={handleTouchStart}
      >
        {/* Layer 1: RAW IMAGE (Full background, untouched) */}
        <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
          <img
            src={rawImageUrl}
            alt="Raw Sonar Frame"
            className="w-full h-full object-contain pointer-events-none"
          />
        </div>

        {/* Layer 2: ENHANCED IMAGE (Clipped overlay) */}
        <div
          className="absolute inset-0 flex items-center justify-center pointer-events-none"
          style={{
            clipPath: `inset(0 0 0 ${sliderPosition}%)`,
          }}
        >
          <img
            src={activeEnhancedUrl}
            alt="Enhanced Sonar Frame"
            className="w-full h-full object-contain pointer-events-none"
          />
        </div>

        {/* Optional YOLO Detections Overlay */}
        {showDetections && detections && detections.length > 0 && (
          <div
            className="absolute inset-0 pointer-events-none"
            style={{
              clipPath: `inset(0 0 0 ${sliderPosition}%)`,
            }}
          >
            {detections.map((d, i) => {
              // Normalized bounding box rendering assumption: scaled to container
              // Detections are [x, y, w, h] in image space
              return (
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
              );
            })}
          </div>
        )}

        {/* Vertical Divider Bar */}
        <div
          className="absolute top-0 bottom-0 w-0.5 bg-white shadow-[0_0_10px_rgba(255,255,255,0.8)] pointer-events-none z-10"
          style={{ left: `${sliderPosition}%` }}
        >
          {/* Circular Grab Handle */}
          <div className="absolute top-1/2 -translate-y-1/2 -translate-x-1/2 w-8 h-8 rounded-full bg-white text-gray-800 shadow-xl border border-gray-300 flex items-center justify-center transition-transform hover:scale-110 active:scale-95">
            <MoveHorizontal className="w-4 h-4 text-gray-700" />
          </div>
        </div>

        {/* Labels Overlay */}
        {/* Left Side Label (RAW) */}
        <div className="absolute top-4 left-4 z-20 pointer-events-none bg-black/75 backdrop-blur-sm border border-white/15 px-3 py-1.5 rounded-lg flex items-center gap-2">
          <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
          <span className="text-[11px] font-mono font-semibold text-white tracking-wider uppercase">
            Raw Sonar (Untouched)
          </span>
          {rawSha256 && (
            <span className="text-[9px] font-mono text-emerald-300/80 bg-white/10 px-1.5 py-0.5 rounded">
              {rawSha256.slice(0, 8)}...
            </span>
          )}
        </div>

        {/* Right Side Label (ENHANCED) */}
        <div className="absolute top-4 right-4 z-20 pointer-events-none bg-black/75 backdrop-blur-sm border border-white/15 px-3 py-1.5 rounded-lg flex items-center gap-2">
          <Eye className="w-3.5 h-3.5 text-sky-400" />
          <span className="text-[11px] font-mono font-semibold text-white tracking-wider uppercase">
            Enhanced ({displayMode === "pseudocolor" ? colormapName : "Acoustic Grayscale"})
          </span>
        </div>

        {/* Bottom Split Indicator */}
        <div className="absolute bottom-3 inset-x-0 flex justify-center pointer-events-none z-20">
          <div className="bg-black/60 backdrop-blur-sm px-3 py-1 rounded-full text-[10px] font-mono text-white/80 border border-white/10">
            Drag divider to compare • {Math.round(sliderPosition)}% Enhanced
          </div>
        </div>
      </div>
    </div>
  );
};
