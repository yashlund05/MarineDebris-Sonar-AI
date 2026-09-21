import React, { useEffect, useRef } from "react";
import { LiveFramePayload, LiveTrack, ViewMode, LiveSourceType } from "../types";
import { ConnectionState } from "../useLiveSonarSocket";
import { AlertTriangle, Radio, RefreshCw, Play, Settings } from "lucide-react";

interface LiveSonarCanvasProps {
  frame: LiveFramePayload | null;
  directImageElement?: HTMLImageElement | null;
  tracks: LiveTrack[];
  viewMode: ViewMode;
  sourceType: LiveSourceType;
  connectionState: ConnectionState;
  lastFrameTime: Date | null;
  selectedTrackId: number | null;
  onSelectTrack: (trackId: number) => void;
  showTracks?: boolean;
  showTrails?: boolean;
  showShadows?: boolean;
  isRunning?: boolean;
  onOpenConfig?: () => void;
  onStartDemo?: () => void;
}

// Color palette for maritime sonar detection categories
const CLASS_COLORS: Record<string, string> = {
  debris: "#DC2626",
  gear: "#D97706",
  wreck: "#7C3AED",
  pipe: "#0891B2",
  other: "#16A34A",
  natural: "#475569",
  default: "#C8523B",
};

export const LiveSonarCanvas: React.FC<LiveSonarCanvasProps> = ({
  frame,
  directImageElement,
  tracks,
  viewMode,
  sourceType,
  connectionState,
  lastFrameTime,
  selectedTrackId,
  onSelectTrack,
  showTracks = true,
  showTrails = true,
  showShadows = true,
  isRunning = true,
  onOpenConfig,
  onStartDemo,
}) => {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const containerRef = useRef<HTMLDivElement | null>(null);
  const imageElementRef = useRef<HTMLImageElement | null>(null);
  const lastDrawnImgRef = useRef<HTMLImageElement | null>(null);
  const splitRatio = 0.5;

  // Maintain an HTMLImageElement for canvas drawing to avoid memory leaks
  useEffect(() => {
    if (!imageElementRef.current) {
      const img = new Image();
      img.src = "/demo_frames/marine-debris-aris3k-64.png";
      imageElementRef.current = img;
    }
  }, []);

  // Update and draw onto canvas
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    let animId: number;

    const render = () => {
      // Clear canvas
      ctx.fillStyle = "#0F172A"; // Sonar navy
      ctx.fillRect(0, 0, canvas.width, canvas.height);

      let activeImg: HTMLImageElement | null = null;
      if (directImageElement && directImageElement.complete && directImageElement.naturalWidth > 0) {
        activeImg = directImageElement;
      } else if (frame?.preview_jpeg) {
        const img = imageElementRef.current;
        if (img) {
          const targetSrc = `data:image/jpeg;base64,${frame.preview_jpeg}`;
          if (img.src !== targetSrc) {
            img.src = targetSrc;
          }
          if (img.complete && img.naturalWidth > 0) {
            activeImg = img;
          }
        }
      } else if (imageElementRef.current) {
        const img = imageElementRef.current;
        if (!img.src || img.src === window.location.href) {
          img.src = "/demo_frames/marine-debris-aris3k-64.png";
        }
        if (img.complete && img.naturalWidth > 0) {
          activeImg = img;
        }
      }

      if (!activeImg) {
        // Draw empty sonar grid
        drawSonarGrid(ctx, canvas.width, canvas.height);
        return;
      }

      lastDrawnImgRef.current = activeImg;

      const imgW = activeImg.naturalWidth;
      const imgH = activeImg.naturalHeight;

      // Fit aspect ratio inside canvas
      const scale = Math.min(canvas.width / imgW, canvas.height / imgH);
      const renderW = imgW * scale;
      const renderH = imgH * scale;
      const offsetX = (canvas.width - renderW) / 2;
      const offsetY = (canvas.height - renderH) / 2;

      // Draw background frame according to view mode
      if (viewMode === "SPLIT") {
        const splitX = offsetX + renderW * splitRatio;

        // Draw left side (RAW representation: grayscale contrast)
        ctx.save();
        ctx.beginPath();
        ctx.rect(offsetX, offsetY, renderW * splitRatio, renderH);
        ctx.clip();
        ctx.filter = "contrast(1.1) brightness(0.85) grayscale(0.5)";
        ctx.drawImage(activeImg, offsetX, offsetY, renderW, renderH);
        ctx.restore();

        // Draw right side (ENHANCED representation: enhanced acoustics)
        ctx.save();
        ctx.beginPath();
        ctx.rect(splitX, offsetY, renderW * (1 - splitRatio), renderH);
        ctx.clip();
        ctx.filter = "none";
        ctx.drawImage(activeImg, offsetX, offsetY, renderW, renderH);
        ctx.restore();

        // Draw split boundary line
        ctx.strokeStyle = "#C8523B";
        ctx.lineWidth = 2;
        ctx.setLineDash([4, 4]);
        ctx.beginPath();
        ctx.moveTo(splitX, offsetY);
        ctx.lineTo(splitX, offsetY + renderH);
        ctx.stroke();
        ctx.setLineDash([]);

        // Split labels
        ctx.font = "bold 10px monospace";
        ctx.fillStyle = "rgba(242, 239, 231, 0.75)";
        ctx.fillText("RAW SIGNAL", offsetX + 8, offsetY + 18);
        ctx.fillText("ENHANCED + AI", splitX + 8, offsetY + 18);
      } else {
        // Full frame view
        ctx.save();
        if (viewMode === "RAW") {
          ctx.filter = "contrast(1.1) brightness(0.85) grayscale(0.5)";
        }
        ctx.drawImage(activeImg, offsetX, offsetY, renderW, renderH);
        ctx.restore();
      }

      // Draw acoustic grid coordinates overlay
      drawAcousticOverlay(ctx, offsetX, offsetY, renderW, renderH, frame?.sonar_metadata?.range_m);

      // Draw AI overlays (Tracks, Detections, Trajectories) if in AI or SPLIT mode
      if (viewMode === "AI" || viewMode === "SPLIT") {
        // Draw Trajectory Trails
        if (showTrails && tracks.length > 0) {
          tracks.forEach((track) => {
            if (!track.trajectory || track.trajectory.length < 2) return;
            const isSelected = track.track_id === selectedTrackId;
            const color = CLASS_COLORS[track.class_name.toLowerCase()] || CLASS_COLORS.default;

            ctx.save();
            ctx.strokeStyle = isSelected ? "#FCD34D" : color;
            ctx.lineWidth = isSelected ? 2.5 : 1.5;
            ctx.lineCap = "round";
            ctx.lineJoin = "round";

            ctx.beginPath();
            track.trajectory.forEach((pt, idx) => {
              const canvasX = offsetX + (pt.x / imgW) * renderW;
              const canvasY = offsetY + (pt.y / imgH) * renderH;
              if (idx === 0) {
                ctx.moveTo(canvasX, canvasY);
              } else {
                ctx.lineTo(canvasX, canvasY);
              }
            });
            ctx.stroke();
            ctx.restore();
          });
        }

        // Draw Bounding Boxes and Labels
        if (showTracks && tracks.length > 0) {
          tracks.forEach((track) => {
            const bx = offsetX + (track.bbox.x / imgW) * renderW;
            const by = offsetY + (track.bbox.y / imgH) * renderH;
            const bw = (track.bbox.w / imgW) * renderW;
            const bh = (track.bbox.h / imgH) * renderH;

            const isConfirmed = track.status === "CONFIRMED";
            const isSelected = track.track_id === selectedTrackId;
            const color = CLASS_COLORS[track.class_name.toLowerCase()] || CLASS_COLORS.default;

            ctx.save();
            // Bounding box
            ctx.strokeStyle = isSelected ? "#FCD34D" : isConfirmed ? color : "rgba(200, 82, 59, 0.6)";
            ctx.lineWidth = isSelected ? 2.5 : 1.5;
            if (!isConfirmed) {
              ctx.setLineDash([4, 2]); // Tentative track dashed line
            }
            ctx.strokeRect(bx, by, bw, bh);
            ctx.setLineDash([]);

            // Acoustic Shadow indicator
            if (showShadows && track.acoustic_shadow === "detected") {
              const shadowH = bh * 0.7;
              ctx.fillStyle = "rgba(15, 23, 42, 0.4)";
              ctx.fillRect(bx, by + bh, bw, shadowH);
              ctx.strokeStyle = "rgba(2, 132, 199, 0.6)";
              ctx.lineWidth = 1;
              ctx.strokeRect(bx, by + bh, bw, shadowH);

              ctx.fillStyle = "#38BDF8";
              ctx.font = "8px monospace";
              ctx.fillText("SHADOW", bx + 2, by + bh + 10);
            }

            // Target Label Badge
            const labelText = `T-${String(track.track_id).padStart(2, "0")} ${track.class_name} ${Math.round(track.confidence * 100)}%`;
            ctx.font = "bold 10px monospace";
            const textMetrics = ctx.measureText(labelText);
            const badgeW = textMetrics.width + 10;
            const badgeH = 16;
            const badgeY = Math.max(offsetY, by - badgeH - 2);

            ctx.fillStyle = isSelected ? "#B45309" : isConfirmed ? color : "#64748B";
            ctx.fillRect(bx, badgeY, badgeW, badgeH);

            ctx.fillStyle = "#FFFFFF";
            ctx.fillText(labelText, bx + 5, badgeY + 12);

            // Confirmation Indicator Tag
            if (isConfirmed) {
              ctx.fillStyle = "#10B981";
              ctx.beginPath();
              ctx.arc(bx + badgeW - 6, badgeY + 8, 3, 0, Math.PI * 2);
              ctx.fill();
            }

            ctx.restore();
          });
        }
      }
    };

    animId = requestAnimationFrame(render);
    return () => {
      cancelAnimationFrame(animId);
    };
  }, [frame, tracks, viewMode, splitRatio, selectedTrackId, showTracks, showTrails, showShadows]);

  // Adjust canvas resolution dynamically to match container size
  useEffect(() => {
    const container = containerRef.current;
    const canvas = canvasRef.current;
    if (!container || !canvas) return;

    const resizeObserver = new ResizeObserver((entries) => {
      for (const entry of entries) {
        const { width, height } = entry.contentRect;
        if (width > 0 && height > 0) {
          canvas.width = width * window.devicePixelRatio;
          canvas.height = height * window.devicePixelRatio;
        }
      }
    });

    resizeObserver.observe(container);
    return () => resizeObserver.disconnect();
  }, []);

  // Handle canvas click to select active track
  const handleCanvasClick = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current;
    const img = lastDrawnImgRef.current || imageElementRef.current;
    if (!canvas || !img || !img.naturalWidth || tracks.length === 0) return;

    const rect = canvas.getBoundingClientRect();
    const clickX = (e.clientX - rect.left) * window.devicePixelRatio;
    const clickY = (e.clientY - rect.top) * window.devicePixelRatio;

    const imgW = img.naturalWidth;
    const imgH = img.naturalHeight;
    const scale = Math.min(canvas.width / imgW, canvas.height / imgH);
    const renderW = imgW * scale;
    const renderH = imgH * scale;
    const offsetX = (canvas.width - renderW) / 2;
    const offsetY = (canvas.height - renderH) / 2;

    for (const track of tracks) {
      const bx = offsetX + (track.bbox.x / imgW) * renderW;
      const by = offsetY + (track.bbox.y / imgH) * renderH;
      const bw = (track.bbox.w / imgW) * renderW;
      const bh = (track.bbox.h / imgH) * renderH;

      if (clickX >= bx && clickX <= bx + bw && clickY >= by && clickY <= by + bh) {
        onSelectTrack(track.track_id);
        return;
      }
    }
  };

  return (
    <div
      ref={containerRef}
      className="relative w-full h-full min-h-[480px] bg-[#0A1118] rounded-2xl overflow-hidden border border-border-subtle shadow-inner flex items-center justify-center select-none"
    >
      <canvas
        ref={canvasRef}
        className="w-full h-full block cursor-crosshair"
        onClick={handleCanvasClick}
      />

      {/* High-Contrast Live vs Replay Indicator */}
      <div className="absolute top-3 left-3 flex items-center gap-2 z-10">
        {!isRunning ? (
          <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-slate-500/20 border border-slate-500/40 text-slate-300 font-mono text-[11px] font-semibold tracking-wide shadow-sm backdrop-blur-sm">
            <span className="w-2 h-2 rounded-full bg-slate-400" />
            <span>STANDBY</span>
          </div>
        ) : sourceType === "demo" ? (
          <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-purple-500/20 border border-purple-500/40 text-purple-300 font-mono text-[11px] font-bold tracking-wide shadow-sm backdrop-blur-sm">
            <span className="w-2 h-2 rounded-full bg-purple-400 animate-ping" />
            <span>🎬 DEMO STREAM</span>
          </div>
        ) : sourceType === "replay" ? (
          <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-amber-500/20 border border-amber-500/40 text-amber-300 font-mono text-[11px] font-bold tracking-wide shadow-sm backdrop-blur-sm">
            <span className="w-2 h-2 rounded-full bg-amber-400 animate-pulse" />
            <span>REPLAY STREAM</span>
          </div>
        ) : (
          <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-emerald-500/20 border border-emerald-500/40 text-emerald-300 font-mono text-[11px] font-bold tracking-wide shadow-sm backdrop-blur-sm">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping" />
            <Radio className="w-3 h-3 text-emerald-400" />
            <span>LIVE FEED</span>
          </div>
        )}

        <div className="px-2 py-1 rounded-full bg-black/40 border border-white/10 text-white/70 font-mono text-[10px] backdrop-blur-sm">
          {viewMode} VIEW
        </div>
      </div>

      {/* Sonar Frame Metadata Watermark */}
      {frame && isRunning && (
        <div className="absolute top-3 right-3 text-right font-mono text-[10px] text-white/60 space-y-0.5 bg-black/40 p-2 rounded-lg backdrop-blur-sm border border-white/10 z-10 pointer-events-none">
          <div>SEQ: #{frame.sequence_number}</div>
          <div>RANGE: {frame.sonar_metadata?.range_m ? `${frame.sonar_metadata.range_m}m` : "NOT_AVAILABLE"}</div>
          <div>CONFIRMED: {frame.metrics.confirmed_targets}</div>
        </div>
      )}

      {/* Standby / Connect Sonar Prompt when stopped */}
      {!isRunning && connectionState !== "CONNECTED" && (
        <div className="absolute inset-0 bg-[#0A1118]/85 backdrop-blur-[2px] flex flex-col items-center justify-center p-6 z-20 text-center space-y-4">
          <div className="w-14 h-14 rounded-2xl bg-accent/15 border border-accent/30 flex items-center justify-center text-accent shadow-lg">
            <Radio className="w-7 h-7" />
          </div>
          <div className="max-w-md space-y-1.5">
            <h2 className="text-base font-bold font-sans text-text-primary tracking-tight">
              Acoustic Camera Standby
            </h2>
            <p className="text-xs text-text-muted leading-relaxed">
              Connect your forward-looking sonar endpoint (ARIS/DIDSON, RTSP feed, or USB capture device) to stream live acoustic frames and run real-time YOLOv8 debris detection.
            </p>
          </div>
          <div className="flex flex-wrap items-center justify-center gap-3 pt-1">
            {onOpenConfig && (
              <button
                type="button"
                onClick={onOpenConfig}
                className="px-4 py-2 rounded-xl bg-accent text-white hover:bg-accent-hover text-xs font-semibold shadow-md transition-all flex items-center gap-1.5 cursor-pointer"
              >
                <Settings className="w-3.5 h-3.5" />
                <span>Configure & Connect Sonar</span>
              </button>
            )}
            {onStartDemo && (
              <button
                type="button"
                onClick={onStartDemo}
                className="px-3.5 py-2 rounded-xl bg-bg-surface hover:bg-bg-elevated border border-border-subtle text-text-secondary hover:text-text-primary text-xs font-medium transition-all flex items-center gap-1.5 cursor-pointer"
              >
                <Play className="w-3.5 h-3.5 text-purple-400 fill-purple-400" />
                <span>Launch Demo Stream</span>
              </button>
            )}
          </div>
        </div>
      )}

      {/* Disconnection / Warning Banner (Never freeze and pretend) */}
      {isRunning && connectionState === "CONNECTION_LOST" && (
        <div className="absolute inset-0 bg-black/75 backdrop-blur-sm flex flex-col items-center justify-center p-6 z-20 text-center space-y-3">
          <div className="w-12 h-12 rounded-full bg-rose-500/20 border border-rose-500/40 flex items-center justify-center text-rose-400">
            <AlertTriangle className="w-6 h-6 animate-pulse" />
          </div>
          <div className="space-y-1">
            <div className="text-rose-300 font-mono font-bold text-sm tracking-wider uppercase">
              CONNECTION LOST
            </div>
            <div className="text-text-muted text-xs">
              Live sonar stream interrupted. Acquisition and AI processing halted.
            </div>
            {lastFrameTime && (
              <div className="text-white/50 font-mono text-[11px] pt-1">
                Last frame received: {lastFrameTime.toLocaleTimeString()} UTC
              </div>
            )}
          </div>
          <div className="flex items-center gap-2 text-amber-300 font-mono text-xs pt-2">
            <RefreshCw className="w-3.5 h-3.5 animate-spin" />
            <span>Attempting automatic reconnection...</span>
          </div>
        </div>
      )}

      {connectionState === "CONNECTING" && (
        <div className="absolute inset-0 bg-black/60 backdrop-blur-sm flex flex-col items-center justify-center p-6 z-20 text-center space-y-2">
          <RefreshCw className="w-6 h-6 text-accent animate-spin" />
          <div className="text-text-primary font-mono text-xs font-semibold">
            Connecting to Live Sonar Source...
          </div>
        </div>
      )}
    </div>
  );
};

// Helper to draw acoustic range rings and crosshairs
function drawSonarGrid(ctx: CanvasRenderingContext2D, width: number, height: number) {
  ctx.save();
  ctx.strokeStyle = "rgba(13, 148, 136, 0.15)";
  ctx.lineWidth = 1;

  const cx = width / 2;
  const cy = height / 2;
  const maxRadius = Math.min(width, height) * 0.45;

  for (let r = maxRadius * 0.25; r <= maxRadius; r += maxRadius * 0.25) {
    ctx.beginPath();
    ctx.arc(cx, cy, r, 0, Math.PI * 2);
    ctx.stroke();
  }

  // Crosshairs
  ctx.beginPath();
  ctx.moveTo(cx, cy - maxRadius);
  ctx.lineTo(cx, cy + maxRadius);
  ctx.moveTo(cx - maxRadius, cy);
  ctx.lineTo(cx + maxRadius, cy);
  ctx.stroke();

  ctx.restore();
}

function drawAcousticOverlay(
  ctx: CanvasRenderingContext2D,
  ox: number,
  oy: number,
  w: number,
  h: number,
  rangeM?: number | null
) {
  ctx.save();
  ctx.strokeStyle = "rgba(2, 132, 199, 0.2)";
  ctx.lineWidth = 1;
  ctx.setLineDash([2, 6]);

  // Down-range grid lines
  const steps = 4;
  for (let i = 1; i < steps; i++) {
    const y = oy + (h / steps) * i;
    ctx.beginPath();
    ctx.moveTo(ox, y);
    ctx.lineTo(ox + w, y);
    ctx.stroke();

    if (rangeM) {
      const dist = Math.round((rangeM / steps) * i);
      ctx.fillStyle = "rgba(2, 132, 199, 0.5)";
      ctx.font = "8px monospace";
      ctx.fillText(`${dist}m`, ox + 4, y - 3);
    }
  }

  ctx.restore();
}
