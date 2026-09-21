import React from "react";
import { ViewMode, LiveSourceType } from "../types";
import {
  Play,
  Pause,
  Circle,
  Camera,
  FastForward,
} from "lucide-react";

interface ControlsDeckProps {
  isPaused: boolean;
  onTogglePause: () => void;
  isRecording: boolean;
  onToggleRecord: () => void;
  onCaptureSnapshot: () => void;
  viewMode: ViewMode;
  onChangeViewMode: (mode: ViewMode) => void;
  sourceType: LiveSourceType;
  replaySpeed: number;
  onChangeSpeed: (speed: number) => void;
  showTracks: boolean;
  onToggleShowTracks: () => void;
  showTrails: boolean;
  onToggleShowTrails: () => void;
  showShadows: boolean;
  onToggleShowShadows: () => void;
}

export const ControlsDeck: React.FC<ControlsDeckProps> = ({
  isPaused,
  onTogglePause,
  isRecording,
  onToggleRecord,
  onCaptureSnapshot,
  viewMode,
  onChangeViewMode,
  sourceType,
  replaySpeed,
  onChangeSpeed,
  showTracks,
  onToggleShowTracks,
  showTrails,
  onToggleShowTrails,
  showShadows,
  onToggleShowShadows,
}) => {
  const viewModes: ViewMode[] = ["RAW", "ENHANCED", "AI", "SPLIT"];
  const speeds = [0.25, 0.5, 1.0, 2.0, 4.0];

  return (
    <div className="w-full bg-bg-surface border border-border-subtle rounded-xl p-3 flex flex-wrap items-center justify-between gap-3 shadow-card select-none">
      {/* Primary Playback & Recording */}
      <div className="flex items-center gap-2">
        <button
          onClick={onTogglePause}
          className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all shadow-sm ${
            isPaused
              ? "bg-emerald-600 text-white hover:bg-emerald-700"
              : "bg-[#19313A] text-white hover:bg-[#254652]"
          }`}
        >
          {isPaused ? <Play className="w-3.5 h-3.5 fill-current" /> : <Pause className="w-3.5 h-3.5 fill-current" />}
          <span>{isPaused ? "Resume" : "Pause"}</span>
        </button>

        <button
          onClick={onToggleRecord}
          className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all border ${
            isRecording
              ? "bg-red-500/15 border-red-500 text-red-600 animate-pulse"
              : "bg-bg-elevated border-border-subtle text-text-primary hover:bg-bg-subtle"
          }`}
        >
          <Circle className={`w-3 h-3 ${isRecording ? "fill-red-600 text-red-600" : "text-text-muted"}`} />
          <span>{isRecording ? "● RECORDING" : "Record"}</span>
        </button>

        <button
          onClick={onCaptureSnapshot}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-bg-elevated border border-border-subtle text-text-primary hover:bg-bg-subtle transition-all"
        >
          <Camera className="w-3.5 h-3.5 text-accent" />
          <span>Snapshot</span>
        </button>
      </div>

      {/* View Mode Switcher */}
      <div className="flex items-center p-1 rounded-lg bg-bg-elevated border border-border-subtle">
        {viewModes.map((mode) => (
          <button
            key={mode}
            onClick={() => onChangeViewMode(mode)}
            className={`px-2.5 py-1 rounded-md text-[11px] font-mono font-semibold transition-all ${
              viewMode === mode
                ? "bg-[#19313A] text-white shadow-sm"
                : "text-text-secondary hover:text-text-primary"
            }`}
          >
            {mode}
          </button>
        ))}
      </div>

      {/* Overlays Toggles */}
      <div className="flex items-center gap-1 font-mono text-[11px]">
        <button
          onClick={onToggleShowTracks}
          className={`px-2 py-1 rounded border transition-all ${
            showTracks
              ? "bg-[#19313A] text-white border-[#19313A]"
              : "bg-bg-elevated text-text-muted border-border-subtle"
          }`}
        >
          Tracks
        </button>
        <button
          onClick={onToggleShowTrails}
          className={`px-2 py-1 rounded border transition-all ${
            showTrails
              ? "bg-[#19313A] text-white border-[#19313A]"
              : "bg-bg-elevated text-text-muted border-border-subtle"
          }`}
        >
          Trails
        </button>
        <button
          onClick={onToggleShowShadows}
          className={`px-2 py-1 rounded border transition-all ${
            showShadows
              ? "bg-[#19313A] text-white border-[#19313A]"
              : "bg-bg-elevated text-text-muted border-border-subtle"
          }`}
        >
          Shadows
        </button>
      </div>

      {/* Replay Speed (if replay source) */}
      {sourceType === "replay" && (
        <div className="flex items-center gap-1.5 font-mono text-xs border-l border-border-subtle pl-3">
          <FastForward className="w-3.5 h-3.5 text-text-muted" />
          <span className="text-text-muted text-[11px]">SPEED:</span>
          <div className="flex items-center gap-0.5">
            {speeds.map((s) => (
              <button
                key={s}
                onClick={() => onChangeSpeed(s)}
                className={`px-1.5 py-0.5 rounded text-[10px] ${
                  replaySpeed === s
                    ? "bg-accent text-white font-bold"
                    : "text-text-muted hover:text-text-primary bg-bg-elevated"
                }`}
              >
                {s}x
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
