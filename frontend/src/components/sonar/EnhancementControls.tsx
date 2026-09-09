import React, { useState } from "react";
import {
  SlidersHorizontal,
  ChevronDown,
  ChevronUp,
  RefreshCw,
  Palette,
  Cpu,
  Waves,
  Sliders,
  AlertTriangle,
} from "lucide-react";
import { SonarEnhancementConfig, PaletteItem } from "../../types/sonarEnhancement";

interface EnhancementControlsProps {
  config: SonarEnhancementConfig;
  onChange: (updated: Partial<SonarEnhancementConfig>) => void;
  onApply: () => void;
  onRecolorFast: (colormap: string) => void;
  palettes: PaletteItem[];
  isLoading: boolean;
  activeFilename?: string;
}

export const EnhancementControls: React.FC<EnhancementControlsProps> = ({
  config,
  onChange,
  onApply,
  onRecolorFast,
  palettes,
  isLoading,
  activeFilename,
}) => {
  const [showAdvanced, setShowAdvanced] = useState<boolean>(false);

  const handlePaletteSelect = (paletteId: string) => {
    onChange({ colormap: paletteId });
    onRecolorFast(paletteId);
  };

  return (
    <div className="bg-bg-surface border border-border-subtle rounded-2xl p-5 shadow-sm space-y-5">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-border-subtle pb-3">
        <div className="space-y-0.5">
          <div className="flex items-center gap-2">
            <SlidersHorizontal className="w-4 h-4 text-accent" />
            <h3 className="font-semibold text-sm text-text-primary">Enhancement Parameters</h3>
          </div>
          {activeFilename && (
            <p className="text-[11px] font-mono text-text-muted">
              Target: <span className="text-text-secondary font-medium">{activeFilename}</span>
            </p>
          )}
        </div>
        <button
          type="button"
          onClick={onApply}
          disabled={isLoading}
          title="Apply current filter parameters to the active sonar image"
          className="flex items-center gap-1.5 px-3.5 py-1.5 bg-accent hover:bg-accent-hover text-white text-xs font-semibold rounded-xl transition shadow-sm disabled:opacity-50"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? "animate-spin" : ""}`} />
          <span>{isLoading ? "Filtering..." : "Apply Filters"}</span>
        </button>
      </div>

      {/* 1. Pseudocolor Visualization Palettes */}
      <div className="space-y-2">
        <div className="flex items-center justify-between text-xs">
          <div className="flex items-center gap-1.5 font-medium text-text-secondary">
            <Palette className="w-3.5 h-3.5 text-sonar-amber" />
            <span>Pseudocolor Display Palette</span>
          </div>
          <span className="text-[10px] font-mono text-text-muted">Instant Recolor</span>
        </div>

        <div className="grid grid-cols-4 gap-2">
          {palettes.map((p) => {
            const isSelected = config.colormap === p.id;
            return (
              <button
                key={p.id}
                type="button"
                onClick={() => handlePaletteSelect(p.id)}
                className={`flex flex-col items-center justify-center p-2 rounded-xl text-xs font-medium border transition-all ${
                  isSelected
                    ? "border-accent bg-accent-subtle/40 text-accent font-semibold shadow-sm"
                    : "border-border-subtle bg-bg-elevated/40 text-text-secondary hover:border-border-default hover:bg-bg-elevated"
                }`}
              >
                <span className="capitalize">{p.name.split(" ")[0]}</span>
              </button>
            );
          })}
        </div>
      </div>

      {/* 2. Core Acoustic Radiometric Filtering */}
      <div className="space-y-3 pt-2">
        <div className="text-xs font-medium text-text-secondary flex items-center gap-1.5">
          <Waves className="w-3.5 h-3.5 text-accent" />
          <span>Core Acoustic Radiometric Filters</span>
        </div>

        {/* 2D-FFT Stripe Filter */}
        <div className="flex items-center justify-between p-3 rounded-xl bg-bg-elevated/60 border border-border-subtle text-xs">
          <div>
            <div className="font-semibold text-text-primary">2D-FFT Stripe Noise Filter</div>
            <div className="text-[11px] text-text-muted">Suppresses periodic beam-acquisition striping</div>
          </div>
          <input
            type="checkbox"
            checked={config.stripe_noise_filter}
            onChange={(e) => onChange({ stripe_noise_filter: e.target.checked })}
            className="w-4 h-4 rounded text-accent focus:ring-accent accent-accent cursor-pointer"
          />
        </div>

        {/* CLAHE Equalization */}
        <div className="p-3 rounded-xl bg-bg-elevated/60 border border-border-subtle text-xs space-y-2">
          <div className="flex items-center justify-between">
            <div>
              <div className="font-semibold text-text-primary">Acoustic CLAHE Equalization</div>
              <div className="text-[11px] text-text-muted">Local contrast equalization across backscatter range</div>
            </div>
            <input
              type="checkbox"
              checked={config.clahe}
              onChange={(e) => onChange({ clahe: e.target.checked })}
              className="w-4 h-4 rounded text-accent focus:ring-accent accent-accent cursor-pointer"
            />
          </div>

          {config.clahe && (
            <div className="pt-2 border-t border-border-subtle/80 space-y-1">
              <div className="flex justify-between text-[11px] text-text-secondary">
                <span>Clip Limit</span>
                <span className="font-mono font-semibold">{config.clahe_clip_limit}</span>
              </div>
              <input
                type="range"
                min={0.005}
                max={0.05}
                step={0.005}
                value={config.clahe_clip_limit}
                onChange={(e) => onChange({ clahe_clip_limit: parseFloat(e.target.value) })}
                className="w-full accent-accent cursor-pointer h-1.5 bg-bg-subtle rounded-lg"
              />
            </div>
          )}
        </div>
      </div>

      {/* 3. ML Detection Integration (Strict Separation Guard) */}
      <div className="p-3 rounded-xl bg-bg-elevated/60 border border-border-subtle text-xs space-y-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-1.5 font-semibold text-text-primary">
            <Cpu className="w-3.5 h-3.5 text-accent" />
            <span>Detection Model Inference</span>
          </div>
          <input
            type="checkbox"
            checked={config.run_detection}
            onChange={(e) => onChange({ run_detection: e.target.checked })}
            className="w-4 h-4 rounded text-accent focus:ring-accent accent-accent cursor-pointer"
          />
        </div>

        {config.run_detection && (
          <div className="pt-2 border-t border-border-subtle/80 space-y-2.5">
            <div>
              <div className="flex justify-between text-[11px] text-text-secondary pb-1">
                <span>Inference Matrix Input</span>
                <span className="font-mono font-medium text-emerald-600">Strictly Grayscale</span>
              </div>
              <div className="grid grid-cols-2 gap-2">
                <button
                  type="button"
                  onClick={() => onChange({ detection_input_mode: "enhanced_grayscale" })}
                  className={`p-1.5 rounded-lg text-[11px] border font-medium ${
                    config.detection_input_mode === "enhanced_grayscale"
                      ? "border-accent bg-accent-subtle/50 text-accent font-semibold"
                      : "border-border-subtle bg-bg-surface text-text-secondary"
                  }`}
                >
                  Enhanced Grayscale
                </button>
                <button
                  type="button"
                  onClick={() => onChange({ detection_input_mode: "raw" })}
                  className={`p-1.5 rounded-lg text-[11px] border font-medium ${
                    config.detection_input_mode === "raw"
                      ? "border-accent bg-accent-subtle/50 text-accent font-semibold"
                      : "border-border-subtle bg-bg-surface text-text-secondary"
                  }`}
                >
                  Raw Grayscale
                </button>
              </div>
            </div>

            <div className="p-2 bg-sonar-amber/10 border border-sonar-amber/20 rounded-lg flex items-start gap-1.5 text-[10px] text-sonar-amber">
              <AlertTriangle className="w-3.5 h-3.5 flex-shrink-0 mt-0.5" />
              <span>Pseudocolor is presentation-only and mathematically prohibited from model input.</span>
            </div>
          </div>
        )}
      </div>

      {/* 4. Collapsible Advanced Acoustic Settings */}
      <div className="pt-1">
        <button
          type="button"
          onClick={() => setShowAdvanced(!showAdvanced)}
          className="flex items-center justify-between w-full text-xs font-medium text-text-muted hover:text-text-secondary transition"
        >
          <div className="flex items-center gap-1.5">
            <Sliders className="w-3.5 h-3.5" />
            <span>Advanced Acoustic Signal Settings</span>
          </div>
          {showAdvanced ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
        </button>

        {showAdvanced && (
          <div className="mt-3 p-3 rounded-xl bg-bg-elevated/40 border border-border-subtle text-xs space-y-3">
            {/* Decibel Conversion */}
            <div className="flex items-center justify-between">
              <div>
                <div className="font-medium text-text-primary">Decibel (dB) Conversion</div>
                <div className="text-[10px] text-text-muted">Auto-gated: skipped safely on rendered 8-bit PNGs</div>
              </div>
              <input
                type="checkbox"
                checked={config.convert_to_db}
                onChange={(e) => onChange({ convert_to_db: e.target.checked })}
                className="w-4 h-4 rounded text-accent focus:ring-accent accent-accent cursor-pointer"
              />
            </div>

            {/* Homomorphic Sharpening */}
            <div className="flex items-center justify-between pt-2 border-t border-border-subtle/60">
              <div>
                <div className="font-medium text-text-primary flex items-center gap-1.5">
                  <span>Homomorphic Sharpening</span>
                  <span className="text-[9px] bg-amber-100 text-amber-800 px-1.5 py-0.2 rounded font-mono">Experimental</span>
                </div>
                <div className="text-[10px] text-text-muted">Frequency-domain high-boost filter (default: OFF)</div>
              </div>
              <input
                type="checkbox"
                checked={config.sharpening}
                onChange={(e) => onChange({ sharpening: e.target.checked })}
                className="w-4 h-4 rounded text-accent focus:ring-accent accent-accent cursor-pointer"
              />
            </div>

            {/* Gain Normalization (BAC/EGN) */}
            <div className="flex items-center justify-between pt-2 border-t border-border-subtle/60">
              <div>
                <div className="font-medium text-text-primary flex items-center gap-1.5">
                  <span>Beam Angle Gain Normalization (BAC)</span>
                  <span className="text-[9px] bg-sky-100 text-sky-800 px-1.5 py-0.2 rounded font-mono">Metadata-Gated</span>
                </div>
                <div className="text-[10px] text-text-muted">Requires sensor telemetry altitude/slant-range metadata</div>
              </div>
              <input
                type="checkbox"
                checked={config.gain_normalization}
                onChange={(e) => onChange({ gain_normalization: e.target.checked })}
                className="w-4 h-4 rounded text-accent focus:ring-accent accent-accent cursor-pointer"
              />
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
