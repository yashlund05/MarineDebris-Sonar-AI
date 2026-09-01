import React, { useEffect, useRef, useState } from "react";
import {
  ZoomIn,
  ZoomOut,
  RotateCcw,
  Crosshair,
  AlertCircle,
  Maximize2,
  Minimize2,
  Scan,
} from "lucide-react";
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
  const { sonarMode, sonarChannel } = useAppStore();
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const containerRef = useRef<HTMLDivElement | null>(null);

  const [image, setImage] = useState<HTMLImageElement | null>(null);
  const [imageLoaded, setImageLoaded] = useState<boolean>(false);
  const [imageError, setImageError] = useState<boolean>(false);
  const [isFullscreen, setIsFullscreen] = useState<boolean>(false);

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

    canvas.width = image.naturalWidth || 1024;
    canvas.height = image.naturalHeight || 600;

    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.save();
    ctx.imageSmoothingEnabled = true;
    ctx.imageSmoothingQuality = "high";
    ctx.drawImage(image, 0, 0, canvas.width, canvas.height);
    ctx.restore();
  }, [image, imageLoaded]);

  const imgWidth = image?.naturalWidth || 1024;
  const imgHeight = image?.naturalHeight || 600;

  const toggleFullscreen = () => {
    if (!containerRef.current) return;
    if (!document.fullscreenElement) {
      containerRef.current.requestFullscreen().catch(() => {});
      setIsFullscreen(true);
    } else {
      document.exitFullscreen().catch(() => {});
      setIsFullscreen(false);
    }
  };

  const fitToScreen = () => {
    if (!containerRef.current || !imgWidth || !imgHeight) return;
    const { clientWidth, clientHeight } = containerRef.current;
    const scaleX = (clientWidth - 40) / imgWidth;
    const scaleY = (clientHeight - 40) / imgHeight;
    const fitScale = Math.min(scaleX, scaleY, 1.0);
    setZoom(fitScale > 0 ? fitScale : 1.0);
  };

  return (
    <div
      ref={containerRef}
      className="flex flex-col h-full bg-bg-surface border border-border-subtle rounded-2xl overflow-hidden shadow-card"
    >
      {/* Top Floating/Integrated Toolbar */}
      <div className="p-2.5 border-b border-border-subtle bg-slate-50/80 flex flex-wrap items-center justify-between gap-3">
        <SonarToggle />

        {/* Viewport Action Controls */}
        <div className="flex items-center gap-1 bg-bg-surface border border-border-subtle p-1 rounded-xl text-xs shadow-subtle">
          <button
            type="button"
            onClick={() => setZoom((z) => Math.min(z * 1.25, 8.0))}
            className="p-1.5 hover:bg-slate-100 rounded-lg text-text-secondary hover:text-text-primary transition-all"
            title="Zoom In (+)"
          >
            <ZoomIn className="w-3.5 h-3.5" />
          </button>
          <span className="font-mono text-xs text-text-primary px-2 font-medium">
            {Math.round(zoom * 100)}%
          </span>
          <button
            type="button"
            onClick={() => setZoom((z) => Math.max(z * 0.8, 0.25))}
            className="p-1.5 hover:bg-slate-100 rounded-lg text-text-secondary hover:text-text-primary transition-all"
            title="Zoom Out (-)"
          >
            <ZoomOut className="w-3.5 h-3.5" />
          </button>
          <div className="h-3.5 w-px bg-border-subtle mx-0.5" />
          <button
            type="button"
            onClick={fitToScreen}
            className="p-1.5 hover:bg-slate-100 rounded-lg text-text-secondary hover:text-text-primary transition-all"
            title="Fit to Screen"
          >
            <Scan className="w-3.5 h-3.5" />
          </button>
          <button
            type="button"
            onClick={resetView}
            className="p-1.5 hover:bg-slate-100 rounded-lg text-text-secondary hover:text-text-primary transition-all"
            title="Reset Pan & Zoom"
          >
            <RotateCcw className="w-3.5 h-3.5" />
          </button>
          <div className="h-3.5 w-px bg-border-subtle mx-0.5" />
          <button
            type="button"
            onClick={toggleFullscreen}
            className="p-1.5 hover:bg-slate-100 rounded-lg text-text-secondary hover:text-text-primary transition-all"
            title={isFullscreen ? "Exit Fullscreen" : "Fullscreen Workstation"}
          >
            {isFullscreen ? <Minimize2 className="w-3.5 h-3.5" /> : <Maximize2 className="w-3.5 h-3.5" />}
          </button>
        </div>
      </div>

      {/* Main Interactive Sonar Viewport */}
      <div
        className={`relative flex-1 bg-slate-900 overflow-hidden cursor-crosshair select-none flex items-center justify-center ${
          isPanning ? "cursor-grabbing" : "cursor-grab"
        }`}
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onWheel={handleWheel}
      >
        {imageError ? (
          <div className="flex flex-col items-center justify-center p-8 text-center space-y-3 text-slate-400">
            <AlertCircle className="w-8 h-8 text-amber-400" />
            <p className="text-sm font-semibold text-slate-200">
              Acoustic Sonar Strip Not Available
            </p>
            <p className="text-xs max-w-sm text-slate-400">
              The acoustic waterfall swath has not yet been parsed or preprocessed for this survey session.
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

            {/* SVG Detection & Segmentation Overlay */}
            {imageLoaded && (
              <DetectionOverlay
                detections={detections}
                imageWidth={imgWidth}
                imageHeight={imgHeight}
              />
            )}
          </div>
        )}

        {/* Viewport Technical Overlay */}
        <div className="absolute bottom-3 right-3 px-3 py-1 bg-slate-900/85 backdrop-blur border border-slate-700 rounded-lg text-[11px] font-mono text-slate-300 pointer-events-none flex items-center gap-2 shadow-lg">
          <Crosshair className="w-3.5 h-3.5 text-sky-400" />
          <span>{imgWidth}×{imgHeight} px</span>
          <span>•</span>
          <span>{detections.length} acoustic targets</span>
        </div>
      </div>
    </div>
  );
};

export default SonarViewer;
