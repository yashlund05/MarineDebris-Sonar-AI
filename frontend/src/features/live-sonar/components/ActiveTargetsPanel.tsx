import React from "react";
import { LiveTrack, EvidenceRecord } from "../types";
import {
  ShieldCheck,
  Camera,
  ChevronRight,
  X,
  Radio,
  Compass,
} from "lucide-react";

interface ActiveTargetsPanelProps {
  tracks: LiveTrack[];
  selectedTrackId: number | null;
  onSelectTrack: (trackId: number | null) => void;
  onCaptureSnapshot: (trackId?: number) => void;
  evidenceList: EvidenceRecord[];
}

const CLASS_BADGE_COLORS: Record<string, string> = {
  debris: "bg-red-50 text-red-700 border-red-200",
  gear: "bg-amber-50 text-amber-700 border-amber-200",
  wreck: "bg-purple-50 text-purple-700 border-purple-200",
  pipe: "bg-cyan-50 text-cyan-700 border-cyan-200",
  other: "bg-emerald-50 text-emerald-700 border-emerald-200",
  natural: "bg-slate-50 text-slate-700 border-slate-200",
  default: "bg-stone-50 text-stone-700 border-stone-200",
};

export const ActiveTargetsPanel: React.FC<ActiveTargetsPanelProps> = ({
  tracks,
  selectedTrackId,
  onSelectTrack,
  onCaptureSnapshot,
  evidenceList,
}) => {
  const selectedTrack = tracks.find((t) => t.track_id === selectedTrackId);
  const trackEvidence = evidenceList.filter((e) => e.track_id === selectedTrackId);

  return (
    <div className="w-full h-full flex flex-col bg-bg-surface border border-border-subtle rounded-xl overflow-hidden shadow-card">
      {/* Panel Header */}
      <div className="p-3 border-b border-border-subtle flex items-center justify-between bg-bg-elevated/40">
        <div className="flex items-center gap-2">
          <Radio className="w-4 h-4 text-accent" />
          <h3 className="font-semibold text-text-primary text-xs tracking-tight">Active Sonar Targets</h3>
        </div>
        <span className="font-mono text-[11px] font-bold px-2 py-0.5 rounded bg-bg-surface border border-border-subtle text-text-secondary">
          {tracks.length}
        </span>
      </div>

      {/* Target List */}
      <div className="flex-1 overflow-y-auto p-2 space-y-1.5 min-h-[160px]">
        {tracks.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center p-6 text-center text-text-muted space-y-1">
            <Radio className="w-6 h-6 text-text-muted/40 animate-pulse" />
            <span className="text-xs">No active targets in acoustic beam</span>
            <span className="text-[11px] text-text-muted/70">Detections confirmed over 3+ frames will appear here</span>
          </div>
        ) : (
          tracks.map((track) => {
            const isSelected = track.track_id === selectedTrackId;
            const isConfirmed = track.status === "CONFIRMED";
            const badgeClass = CLASS_BADGE_COLORS[track.class_name.toLowerCase()] || CLASS_BADGE_COLORS.default;

            return (
              <div
                key={track.track_id}
                onClick={() => onSelectTrack(track.track_id)}
                className={`p-2.5 rounded-lg border transition-all cursor-pointer flex items-center justify-between gap-2 ${
                  isSelected
                    ? "bg-[#19313A] text-white border-[#19313A] shadow-sm"
                    : "bg-bg-surface border-border-subtle hover:bg-bg-elevated text-text-primary"
                }`}
              >
                <div className="flex items-center gap-2 min-w-0">
                  <div
                    className={`font-mono text-[11px] font-bold px-1.5 py-0.5 rounded ${
                      isSelected ? "bg-white/20 text-white" : "bg-bg-elevated text-text-primary"
                    }`}
                  >
                    T-{String(track.track_id).padStart(2, "0")}
                  </div>

                  <div className="truncate">
                    <div className="flex items-center gap-1.5">
                      <span className="text-xs font-semibold truncate capitalize">{track.class_name}</span>
                      <span
                        className={`text-[10px] font-mono px-1 rounded border uppercase ${
                          isSelected ? "bg-white/10 text-white border-white/20" : badgeClass
                        }`}
                      >
                        {Math.round(track.confidence * 100)}%
                      </span>
                    </div>
                    <div className={`text-[10px] font-mono ${isSelected ? "text-white/70" : "text-text-muted"}`}>
                      {track.frames_seen} frames · {isConfirmed ? "Confirmed" : "Tentative"}
                    </div>
                  </div>
                </div>

                <div className="flex items-center gap-1 flex-shrink-0">
                  {isConfirmed && <ShieldCheck className={`w-3.5 h-3.5 ${isSelected ? "text-emerald-300" : "text-emerald-600"}`} />}
                  <ChevronRight className={`w-3.5 h-3.5 ${isSelected ? "text-white/80" : "text-text-muted"}`} />
                </div>
              </div>
            );
          })
        )}
      </div>

      {/* Target Inspector Drawer */}
      {selectedTrack && (
        <div className="p-3 border-t border-border-subtle bg-bg-elevated/70 space-y-3 font-mono text-xs max-h-[360px] overflow-y-auto">
          <div className="flex items-center justify-between border-b border-border-subtle pb-2">
            <div className="flex items-center gap-1.5">
              <span className="font-bold text-text-primary">TARGET T-{String(selectedTrack.track_id).padStart(2, "0")}</span>
              <span className={`text-[10px] px-1.5 py-0.2 rounded border uppercase ${CLASS_BADGE_COLORS[selectedTrack.class_name.toLowerCase()] || CLASS_BADGE_COLORS.default}`}>
                {selectedTrack.class_name}
              </span>
            </div>
            <button
              onClick={() => onSelectTrack(null)}
              className="p-1 rounded hover:bg-bg-subtle text-text-muted hover:text-text-primary"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          </div>

          <div className="grid grid-cols-2 gap-2 text-[11px]">
            <div>
              <span className="text-text-muted block text-[10px]">CONFIDENCE</span>
              <span className="font-semibold text-text-primary">{Math.round(selectedTrack.confidence * 100)}%</span>
            </div>
            <div>
              <span className="text-text-muted block text-[10px]">STATUS</span>
              <span className={`font-semibold ${selectedTrack.status === "CONFIRMED" ? "text-emerald-600" : "text-amber-600"}`}>
                {selectedTrack.status}
              </span>
            </div>
            <div>
              <span className="text-text-muted block text-[10px]">OBSERVED</span>
              <span className="text-text-primary">{selectedTrack.frames_seen} frames</span>
            </div>
            <div>
              <span className="text-text-muted block text-[10px]">SHADOW</span>
              <span className="text-text-primary uppercase">{selectedTrack.acoustic_shadow || "UNAVAILABLE"}</span>
            </div>
          </div>

          {/* Telemetry & Georeference */}
          <div className="p-2 rounded bg-bg-surface border border-border-subtle space-y-1 text-[11px]">
            <div className="flex items-center gap-1 text-text-muted text-[10px] font-semibold uppercase">
              <Compass className="w-3 h-3" /> Navigation & Position
            </div>
            <div className="flex justify-between">
              <span className="text-text-muted">LAT/LON:</span>
              <span className="font-semibold text-text-primary">
                {selectedTrack.latitude !== null && selectedTrack.latitude !== undefined && selectedTrack.longitude !== null && selectedTrack.longitude !== undefined
                  ? `${selectedTrack.latitude.toFixed(5)}, ${selectedTrack.longitude.toFixed(5)}`
                  : "NOT_AVAILABLE"}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-text-muted">DEPTH:</span>
              <span className="text-text-primary">
                {selectedTrack.depth_m !== null && selectedTrack.depth_m !== undefined
                  ? `${selectedTrack.depth_m.toFixed(1)} m`
                  : "NOT_AVAILABLE"}
              </span>
            </div>
            {trackEvidence.length > 0 && (
              <div className="flex justify-between text-emerald-600">
                <span>EVIDENCE CROPS:</span>
                <span className="font-semibold">{trackEvidence.length} captured</span>
              </div>
            )}
          </div>

          {/* Action: Snapshot */}
          <button
            onClick={() => onCaptureSnapshot(selectedTrack.track_id)}
            className="w-full flex items-center justify-center gap-1.5 py-1.5 px-3 rounded-lg bg-accent text-white font-medium text-xs hover:bg-accent-hover transition-all shadow-sm"
          >
            <Camera className="w-3.5 h-3.5" />
            <span>Capture Forensic Evidence</span>
          </button>
        </div>
      )}
    </div>
  );
};
