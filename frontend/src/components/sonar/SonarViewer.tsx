import React, { useEffect, useRef, useState } from "react";
import { ZoomIn, ZoomOut, RotateCcw, Crosshair, AlertCircle } from "lucide-react";
import { Detection } from "../../types";
import { useAppStore } from "../../store/useAppStore";
import { useSonarViewer } from "../../hooks/useSonarViewer";
import { SonarToggle } from "./SonarToggle";
import { DetectionOverlay } from "./DetectionOverlay";
import { surveysApi } from "../../api/surveys";

interface SonarViewerProps {
  surveyId: string;
  detections: Detection[];
}

export const SonarViewer: React.FC<SonarViewerProps> = ({ surveyId, detections }) => {
  const { sonarMode, sonarChannel, showOverlay } = useAppStore();
  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  const [image, setImage] = useState<HTMLImageElement | null>(null);
  const [imageLoaded, setImageLoaded] = useState<boolean>(false);
  const [imageError, setImageError] = useState<boolean>(false);

  const {
    zoom,
    setZoom,
    pan,
    isPanning,
    handleMouseDown,
    handleMouseMove,
    handleMouseUp,
    handleWheel,
    resetView,
  } = useSonarViewer();

  // Load sonar strip image
  useEffect(() => {
    setImageLoaded(false);
    setImageError(false);

    const img = new Image();
    img.crossOrigin = "anonymous";
    img.src = surveysApi.getSonarImageUrl(surveyId, sonarChannel, sonarMode);

    img.onload = () => {
      setImage(img);
      setImageLoaded(true);
    };

    img.onerror = () => {
      setImageError(true);
    };
  }, [surveyId, sonarChannel, sonarMode]);

  // Render on canvas
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas || !image || !imageLoaded) return;

    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    // Set canvas dimensions to match container or image
    canvas.width = image.naturalWidth || 1024;
    canvas.height = image.naturalHeight || 600;

    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.save();

    // High quality image smoothing for sonar acoustic textures
    ctx.imageSmoothingEnabled = true;
    ctx.imageSmoothingQuality = "high";

    ctx.drawImage(image, 0, 0, canvas.width, canvas.height);
    ctx.restore();
  }, [image, imageLoaded]);

  const imgWidth = image?.naturalWidth || 1024;
  const imgHeight = image?.naturalHeight || 600;

  return (
    <div className="flex flex-col h-full bg-bg-surface border border-border-subtle rounded-2xl overflow-hidden shadow-lg">
      {/* Top Viewer Toolbar */}
      <div className="p-3 border-b border-border-subtle bg-bg-surface flex flex-wrap items-center justify-between gap-3">
        <SonarToggle />

        {/* Zoom & Reset Controls */}
        <div className="flex items-center gap-1 bg-bg-elevated p-1 rounded-xl text-xs">
          <button
            type="button"
            onClick={() => setZoom((z) => Math.min(z * 1.25, 8.0))}
            className="p-1.5 hover:bg-bg-surface rounded-lg text-text-secondary hover:text-text-primary transition-all"
            title="Zoom In"
          >
            <ZoomIn className="w-4 h-4" />
          </button>
          <span className="font-mono text-xs text-text-primary px-2 font-medium">
            {Math.round(zoom * 100)}%
          </span>
          <button
            type="button"
            onClick={() => setZoom((z) => Math.max(z * 0.8, 0.25))}
            className="p-1.5 hover:bg-bg-surface rounded-lg text-text-secondary hover:text-text-primary transition-all"
            title="Zoom Out"
          >
            <ZoomOut className="w-4 h-4" />
          </button>
          <div className="h-4 w-px bg-border-subtle mx-1" />
          <button
            type="button"
            onClick={resetView}
            className="p-1.5 hover:bg-bg-surface rounded-lg text-text-secondary hover:text-text-primary transition-all"
            title="Reset Pan & Zoom"
          >
            <RotateCcw className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Main Interactive Canvas Area */}
      <div
        className={`relative flex-1 bg-bg-primary overflow-hidden cursor-crosshair select-none flex items-center justify-center ${
          isPanning ? "cursor-grabbing" : "cursor-grab"
        }`}
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onWheel={handleWheel}
      >
        {imageError ? (
          <div className="flex flex-col items-center justify-center p-8 text-center space-y-3 text-text-muted">
            <AlertCircle className="w-8 h-8 text-amber-500/80" />
            <p className="text-sm font-medium text-text-primary">
              Sonar Image Not Available
            </p>
            <p className="text-xs max-w-sm">
              The acoustic sonar waterfall strip has not yet been rendered by the processing pipeline.
            </p>
          </div>
        ) : (
          <div
            className="relative transition-transform duration-75 origin-center"
            style={{
              transform: `translate(${pan.x}px, ${pan.y}px) scale(${zoom})`,
            }}
          >
            <canvas
              ref={canvasRef}
              className="block max-w-none shadow-2xl rounded-sm"
              style={{
                width: imgWidth,
                height: imgHeight,
              }}
            />

            {/* SVG Detection Overlay */}
            {showOverlay && imageLoaded && (
              <DetectionOverlay
                detections={detections}
                imageWidth={imgWidth}
                imageHeight={imgHeight}
              />
            )}
          </div>
        )}

        {/* Viewport Info Overlay */}
        <div className="absolute bottom-3 right-3 px-2.5 py-1 bg-bg-primary/80 backdrop-blur border border-border-subtle rounded-lg text-[11px] font-mono text-text-secondary pointer-events-none flex items-center gap-2">
          <Crosshair className="w-3 h-3 text-accent" />
          <span>{imgWidth}x{imgHeight} px</span>
          <span>•</span>
          <span>{detections.length} detections</span>
        </div>
      </div>
    </div>
  );
};
