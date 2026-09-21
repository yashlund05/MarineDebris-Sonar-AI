import React, { useState, useEffect } from "react";
import {
  LiveSessionConfig,
  LiveSourceType,
  PreprocessingProfile,
  DropPolicy,
} from "../types";
import { Radio, Settings, Play, Square } from "lucide-react";

interface ConnectionPanelProps {
  currentConfig: LiveSessionConfig;
  isRunning: boolean;
  onStartSession: (config: LiveSessionConfig) => void;
  onStopSession: () => void;
  isOpen?: boolean;
  onToggleOpen?: (open: boolean) => void;
  connectionError?: string | null;
}

export const ConnectionPanel: React.FC<ConnectionPanelProps> = ({
  currentConfig,
  isRunning,
  onStartSession,
  onStopSession,
  isOpen: propIsOpen,
  onToggleOpen,
  connectionError,
}) => {
  const [config, setConfig] = useState<LiveSessionConfig>(currentConfig);
  const [internalIsOpen, setInternalIsOpen] = useState<boolean>(false);

  const isOpen = propIsOpen !== undefined ? propIsOpen : internalIsOpen;
  const setIsOpen = (val: boolean) => {
    setInternalIsOpen(val);
    onToggleOpen?.(val);
  };

  useEffect(() => {
    setConfig(currentConfig);
  }, [currentConfig]);

  const presets: Record<LiveSourceType, { name: string; uri: string; desc: string }> = {
    native_stub: {
      name: "Native Sonar (ARIS/DIDSON)",
      uri: "aris://192.168.1.50:7000",
      desc: "Sound Metrics ARIS/DIDSON acoustic camera telemetry protocol",
    },
    rtsp: {
      name: "RTSP Video Feed",
      uri: "rtsp://192.168.1.100:554/sonar",
      desc: "Network-attached acoustic camera or top-side video encoder",
    },
    usb: {
      name: "Direct USB / Device",
      uri: "device://0",
      desc: "Local UVC camera or capture card hardware index",
    },
    replay: {
      name: "Replay Stream",
      uri: "datasets/benchmarks/synthetic_acoustic_test.mp4",
      desc: "Deterministic synthetic or recorded survey video stream replay",
    },
    demo: {
      name: "Demo Mode",
      uri: "demo",
      desc: "Built-in ARIS 3000 FLS sonar replay with live AI detection — no setup required",
    },
  };

  const handleSourceTypeChange = (type: LiveSourceType) => {
    setConfig({
      ...config,
      source_type: type,
      source_uri: presets[type].uri,
    });
  };

  const handleConnectClick = () => {
    if (config.source_type === "demo") {
      // If currently on demo, switch to real native sonar and open the configuration drawer!
      const realCfg: LiveSessionConfig = {
        ...config,
        source_type: "native_stub",
        source_uri: presets.native_stub.uri,
      };
      setConfig(realCfg);
      setIsOpen(true);
    } else {
      onStartSession(config);
    }
  };

  const handleFormSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onStartSession(config);
    setIsOpen(false);
  };

  return (
    <div className="w-full bg-bg-surface border border-border-subtle rounded-xl p-3 shadow-card">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-[#19313A] text-white flex items-center justify-center">
            <Radio className="w-4 h-4 text-accent" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xs font-bold text-text-primary uppercase tracking-wider font-mono">
                {presets[config.source_type]?.name || config.source_type}
              </span>
              <span
                className={`w-2 h-2 rounded-full ${
                  isRunning ? "bg-emerald-500 animate-ping" : "bg-text-muted/40"
                }`}
              />
            </div>
            <div className="text-[11px] font-mono text-text-muted truncate max-w-md">
              URI: {config.source_uri}
            </div>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => setIsOpen(!isOpen)}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium border transition-all ${
              isOpen
                ? "bg-accent/15 border-accent text-accent font-semibold"
                : "border-border-subtle hover:bg-bg-elevated text-text-primary"
            }`}
          >
            <Settings className="w-3.5 h-3.5 text-text-muted" />
            <span>{isOpen ? "Close Config" : "Config"}</span>
          </button>

          {isRunning ? (
            <button
              onClick={onStopSession}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-red-600 text-white hover:bg-red-700 transition-all shadow-sm"
            >
              <Square className="w-3.5 h-3.5 fill-current" />
              <span>Stop Stream</span>
            </button>
          ) : (
            <button
              onClick={handleConnectClick}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-accent text-white hover:bg-accent-hover transition-all shadow-sm cursor-pointer"
            >
              <Play className="w-3.5 h-3.5 fill-current" />
              <span>Connect & Run</span>
            </button>
          )}
        </div>
      </div>

      {/* Connection Error Banner */}
      {connectionError && (
        <div className="mt-3 p-3 bg-red-500/10 border border-red-500/25 rounded-xl text-xs font-mono text-red-600 flex flex-wrap items-center justify-between gap-2">
          <div className="flex items-center gap-2">
            <span className="font-bold uppercase tracking-wider">Connection Failed:</span>
            <span>{connectionError}</span>
          </div>
          <button
            type="button"
            onClick={() => setIsOpen(true)}
            className="text-xs font-semibold text-accent underline hover:text-accent-hover"
          >
            Configure Sonar Endpoint
          </button>
        </div>
      )}

      {/* Expanded Configuration Modal / Drawer */}
      {isOpen && (
        <form
          onSubmit={handleFormSubmit}
          className="mt-4 pt-4 border-t border-border-subtle grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 text-xs font-mono"
        >
          {/* Source Selector */}
          <div className="space-y-1.5">
            <label className="text-text-muted block text-[11px] font-semibold uppercase">
              Acoustic Source Type
            </label>
            <select
              value={config.source_type}
              onChange={(e) => handleSourceTypeChange(e.target.value as LiveSourceType)}
              className="w-full p-2 rounded-lg bg-bg-elevated border border-border-subtle text-text-primary text-xs focus:outline-none focus:border-accent"
            >
              <option value="demo">🎬 Demo Mode (Built-in ARIS 3000 sonar)</option>
              <option value="replay">Deterministic Replay (.mp4 / sequence)</option>
              <option value="rtsp">RTSP Network Stream (rtsp://)</option>
              <option value="usb">USB Capture / Direct Camera (device://)</option>
              <option value="native_stub">Native Sonar Stub (ARIS/DIDSON)</option>
            </select>
            <span className="text-[10px] text-text-muted block">
              {presets[config.source_type]?.desc}
            </span>
          </div>

          {/* URI Input */}
          <div className="space-y-1.5">
            <label className="text-text-muted block text-[11px] font-semibold uppercase">
              Source URI / Path
            </label>
            <input
              type="text"
              value={config.source_uri}
              onChange={(e) => setConfig({ ...config, source_uri: e.target.value })}
              className="w-full p-2 rounded-lg bg-bg-elevated border border-border-subtle text-text-primary text-xs focus:outline-none focus:border-accent"
              required
            />
            <span className="text-[10px] text-text-muted block">
              File path or connection endpoint
            </span>
          </div>

          {/* Preprocessing Profile */}
          <div className="space-y-1.5">
            <label className="text-text-muted block text-[11px] font-semibold uppercase">
              Preprocessing Profile
            </label>
            <select
              value={config.preprocessing_profile}
              onChange={(e) =>
                setConfig({
                  ...config,
                  preprocessing_profile: e.target.value as PreprocessingProfile,
                })
              }
              className="w-full p-2 rounded-lg bg-bg-elevated border border-border-subtle text-text-primary text-xs focus:outline-none focus:border-accent"
            >
              <option value="REALTIME">REALTIME (Max speed, minimal CLAHE)</option>
              <option value="BALANCED">BALANCED (Recommended standard)</option>
              <option value="QUALITY">QUALITY (Full denoising & enhancement)</option>
            </select>
          </div>

          {/* Target FPS & Inference FPS */}
          <div className="space-y-1.5">
            <label className="text-text-muted block text-[11px] font-semibold uppercase">
              Target Acq FPS ({config.target_fps}) / Inference FPS ({config.inference_fps})
            </label>
            <div className="grid grid-cols-2 gap-2">
              <input
                type="number"
                min="1"
                max="60"
                value={config.target_fps}
                onChange={(e) =>
                  setConfig({ ...config, target_fps: parseFloat(e.target.value) || 15 })
                }
                className="w-full p-2 rounded-lg bg-bg-elevated border border-border-subtle text-text-primary text-xs"
              />
              <input
                type="number"
                min="1"
                max="30"
                value={config.inference_fps}
                onChange={(e) =>
                  setConfig({ ...config, inference_fps: parseFloat(e.target.value) || 10 })
                }
                className="w-full p-2 rounded-lg bg-bg-elevated border border-border-subtle text-text-primary text-xs"
              />
            </div>
          </div>

          {/* Buffer & Drop Policy */}
          <div className="space-y-1.5">
            <label className="text-text-muted block text-[11px] font-semibold uppercase">
              Drop Policy & Buffer Size ({config.buffer_size})
            </label>
            <select
              value={config.drop_policy}
              onChange={(e) => setConfig({ ...config, drop_policy: e.target.value as DropPolicy })}
              className="w-full p-2 rounded-lg bg-bg-elevated border border-border-subtle text-text-primary text-xs focus:outline-none focus:border-accent"
            >
              <option value="DROP_OLDEST">DROP_OLDEST (Favors lowest latency)</option>
              <option value="FIFO">FIFO (Sequential processing)</option>
              <option value="DROP_NEWEST">DROP_NEWEST (Preserves buffer head)</option>
              <option value="LATEST">LATEST (Ring buffer single latest)</option>
            </select>
          </div>

          {/* Confidence Threshold */}
          <div className="space-y-1.5">
            <label className="text-text-muted block text-[11px] font-semibold uppercase">
              Confidence Threshold ({Math.round(config.confidence_threshold * 100)}%)
            </label>
            <input
              type="range"
              min="0.1"
              max="0.9"
              step="0.05"
              value={config.confidence_threshold}
              onChange={(e) =>
                setConfig({ ...config, confidence_threshold: parseFloat(e.target.value) })
              }
              className="w-full accent-accent"
            />
          </div>

          <div className="col-span-full flex justify-end gap-2 pt-2 border-t border-border-subtle">
            <button
              type="button"
              onClick={() => setIsOpen(false)}
              className="px-3 py-1.5 rounded-lg border border-border-subtle text-text-secondary hover:bg-bg-elevated text-xs"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="px-4 py-1.5 rounded-lg bg-accent text-white hover:bg-accent-hover text-xs font-semibold shadow-sm"
            >
              Apply & Save
            </button>
          </div>
        </form>
      )}
    </div>
  );
};
