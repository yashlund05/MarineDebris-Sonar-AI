import React, { useState, useEffect } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  LiveSessionConfig,
  LiveSessionDetails,
  LiveHealthStatus,
  ViewMode,
  EvidenceRecord,
  LiveMetrics,
} from "../features/live-sonar/types";
import { useLiveSonarSocket } from "../features/live-sonar/useLiveSonarSocket";
import { useDemoPlayer } from "../features/live-sonar/useDemoPlayer";
import { LiveSonarCanvas } from "../features/live-sonar/components/LiveSonarCanvas";
import { LiveMetricsBar } from "../features/live-sonar/components/LiveMetricsBar";
import { ActiveTargetsPanel } from "../features/live-sonar/components/ActiveTargetsPanel";
import { ControlsDeck } from "../features/live-sonar/components/ControlsDeck";
import { ConnectionPanel } from "../features/live-sonar/components/ConnectionPanel";
import { liveSonarApi } from "../api/liveSonar";
import { Radio, Database, Play, Sparkles, StopCircle, RefreshCw } from "lucide-react";

export const LiveSonarPage: React.FC = () => {
  const [sessionId, setSessionId] = useState<string>("session_live_demo");
  const [isDemoMode, setIsDemoMode] = useState<boolean>(true); // Auto-start in demo mode so video is immediately playing!
  const [isRunning, setIsRunning] = useState<boolean>(true);
  const [isRecording, setIsRecording] = useState<boolean>(false);
  const [viewMode, setViewMode] = useState<ViewMode>("AI");
  const [selectedTrackId, setSelectedTrackId] = useState<number | null>(null);
  const [replaySpeed, setReplaySpeed] = useState<number>(1.0);
  const [showTracks, setShowTracks] = useState<boolean>(true);
  const [showTrails, setShowTrails] = useState<boolean>(true);
  const [showShadows, setShowShadows] = useState<boolean>(true);
  const [evidenceList, setEvidenceList] = useState<EvidenceRecord[]>([]);
  const [isConfigOpen, setIsConfigOpen] = useState<boolean>(false);
  const [connectionError, setConnectionError] = useState<string | null>(null);

  const [sessionConfig, setSessionConfig] = useState<LiveSessionConfig>({
    session_id: "session_live_demo",
    name: "ARIS 3000 Sonar Demo Stream",
    source_type: "demo",
    source_uri: "demo",
    target_fps: 15.0,
    inference_fps: 10.0,
    buffer_size: 60,
    drop_policy: "DROP_OLDEST",
    preprocessing_profile: "BALANCED",
    enable_tracking: true,
    enable_recording: false,
    confidence_threshold: 0.25,
    minimum_confirmed_frames: 3,
  });

  // Client-side demo player for instant, continuous authentic ARIS 3000 playback with real YOLOv8 detections
  const demoPlayer = useDemoPlayer({
    enabled: isDemoMode && isRunning,
    speed: replaySpeed,
  });

  // Query live subsystem health
  const { data: health } = useQuery<LiveHealthStatus>({
    queryKey: ["live-sonar-health"],
    queryFn: () => liveSonarApi.getHealth(),
    refetchInterval: 10000,
    retry: false,
  });

  // Connect WebSocket stream for real live hardware sources
  const {
    connectionState,
    latestFrame,
    tracks,
    metrics: socketMetrics,
    lastFrameTime,
    isPaused: isSocketPaused,
    pause: socketPause,
    resume: socketResume,
    setSpeed: socketSetSpeed,
  } = useLiveSonarSocket({
    sessionId: !isDemoMode && isRunning ? sessionId : null,
    autoConnect: !isDemoMode && isRunning,
  });

  // Fetch session details on mount
  useEffect(() => {
    let isMounted = true;
    const checkExistingSession = async () => {
      try {
        const sessions: LiveSessionDetails[] = await liveSonarApi.listSessions();
        if (sessions.length > 0 && isMounted) {
          const active = sessions.find((s: LiveSessionDetails) => s.status === "RUNNING");
          if (active) {
            setSessionId(active.session_id);
            setIsDemoMode(active.source_type === "demo");
            setIsRunning(true);
            setIsRecording(active.is_recording);
          }
        }
      } catch {
        // Standalone fallback: demoPlayer continues seamlessly
      }
    };
    checkExistingSession();
    return () => {
      isMounted = false;
    };
  }, []);

  // Poll evidence records when running backend session
  useEffect(() => {
    if (!isRunning || isDemoMode) return;
    const interval = setInterval(async () => {
      try {
        const ev = await liveSonarApi.getEvidence(sessionId);
        setEvidenceList(ev);
      } catch {
        // Ignore
      }
    }, 5000);
    return () => clearInterval(interval);
  }, [isRunning, isDemoMode, sessionId]);

  // Determine active frame, tracks, metrics, and image
  const activeFrame = isDemoMode
    ? (isRunning ? demoPlayer.currentFramePayload : null)
    : (isRunning ? latestFrame : null);

  const activeTracks = isDemoMode
    ? (isRunning ? demoPlayer.currentFramePayload.tracks : [])
    : (isRunning ? (tracks && tracks.length > 0 ? tracks : latestFrame?.tracks || []) : []);

  const defaultMetrics: LiveMetrics = {
    input_fps: 0,
    inference_fps: 0,
    display_fps: 0,
    latency_ms: 0,
    queue_depth: 0,
    frames_dropped: 0,
    drop_rate: 0,
    active_tracks: 0,
    confirmed_targets: 0,
  };

  const activeMetrics: LiveMetrics = isDemoMode
    ? (isRunning ? demoPlayer.currentFramePayload.metrics : defaultMetrics)
    : (isRunning ? (latestFrame?.metrics || socketMetrics || defaultMetrics) : defaultMetrics);

  const directImage = isDemoMode
    ? (isRunning ? demoPlayer.currentImage : null)
    : null;

  const isPaused = isDemoMode ? !demoPlayer.isPlaying : isSocketPaused;

  const handleStartSession = async (cfg: LiveSessionConfig) => {
    setConnectionError(null);

    if (cfg.source_type === "demo") {
      setIsDemoMode(true);
      setIsRunning(true);
      setSessionConfig(cfg);
      demoPlayer.play();
      return;
    }

    try {
      setIsDemoMode(false);
      setSessionConfig(cfg);
      const session = await liveSonarApi.createSession(cfg);
      setSessionId(session.session_id);
      await liveSonarApi.startSession(session.session_id);
      setIsRunning(true);
      setIsConfigOpen(false);
    } catch (err: any) {
      console.warn("Backend live stream start failed:", err);
      // DO NOT FALL BACK TO DEMO MODE! Keep user on connection configuration!
      setIsRunning(false);
      setIsDemoMode(false);
      demoPlayer.pause();
      const errorMsg =
        err?.response?.data?.detail ||
        err?.message ||
        `Unable to connect to sonar at ${cfg.source_uri}. Please verify sensor power, network cable, and endpoint configuration.`;
      setConnectionError(errorMsg);
      setIsConfigOpen(true);
    }
  };

  const handleStopDemo = () => {
    setIsDemoMode(false);
    setIsRunning(false);
    setIsRecording(false);
    demoPlayer.pause();
    setConnectionError(null);
    // Switch to native sonar hardware default
    setSessionConfig({
      session_id: `session_live_${Date.now()}`,
      name: "ARIS 3000 Sonar Stream",
      source_type: "native_stub",
      source_uri: "aris://192.168.1.50:7000",
      target_fps: 15.0,
      inference_fps: 10.0,
      buffer_size: 60,
      drop_policy: "DROP_OLDEST",
      preprocessing_profile: "BALANCED",
      enable_tracking: true,
      enable_recording: false,
      confidence_threshold: 0.25,
      minimum_confirmed_frames: 3,
    });
    // Open connection configuration drawer so user is ready to connect actual sonar
    setIsConfigOpen(true);
  };

  const handleStopSession = async () => {
    if (isDemoMode) {
      handleStopDemo();
      return;
    }

    try {
      await liveSonarApi.stopSession(sessionId);
    } catch (err: any) {
      console.error("Error stopping live sonar stream:", err);
    } finally {
      setIsRunning(false);
      setIsRecording(false);
    }
  };

  const handleStartDemo = () => {
    setConnectionError(null);
    setIsConfigOpen(false);
    setIsDemoMode(true);
    setIsRunning(true);
    setSessionConfig({
      session_id: "session_live_demo",
      name: "ARIS 3000 Sonar Demo Stream",
      source_type: "demo",
      source_uri: "demo",
      target_fps: 15.0,
      inference_fps: 10.0,
      buffer_size: 60,
      drop_policy: "DROP_OLDEST",
      preprocessing_profile: "BALANCED",
      enable_tracking: true,
      enable_recording: false,
      confidence_threshold: 0.25,
      minimum_confirmed_frames: 3,
    });
    demoPlayer.play();
  };

  const handleTogglePause = () => {
    if (isDemoMode) {
      demoPlayer.togglePlay();
    } else {
      if (isPaused) {
        socketResume();
      } else {
        socketPause();
      }
    }
  };

  const handleToggleRecord = () => {
    setIsRecording(!isRecording);
  };

  const handleSpeedChange = (speed: number) => {
    setReplaySpeed(speed);
    if (!isDemoMode) {
      socketSetSpeed(speed);
    }
  };

  const handleCaptureSnapshot = async (trackId?: number) => {
    if (isDemoMode) {
      const cur = demoPlayer.currentDef;
      const track = cur.tracks.find((t) => t.track_id === trackId) || cur.tracks[0];
      const newEv: EvidenceRecord = {
        evidence_id: `ev_demo_${Date.now()}`,
        session_id: "session_live_demo",
        track_id: track ? track.track_id : 1,
        frame_id: demoPlayer.currentFramePayload.frame_id,
        timestamp_utc: new Date().toISOString(),
        class_name: track ? track.class_name : "marine_debris",
        confidence: track ? track.confidence : 0.92,
        bbox: track
          ? [track.bbox.x, track.bbox.y, track.bbox.w, track.bbox.h]
          : [200, 200, 100, 100],
        raw_crop_path: cur.imageSrc,
        processed_crop_path: cur.imageSrc,
        annotated_crop_path: cur.imageSrc,
        metadata: {
          note: "Captured from authentic ARIS 3000 live sonar demo stream",
          range_m: cur.sonar_metadata.range_m,
          frequency_hz: cur.sonar_metadata.frequency_hz,
        },
      };
      setEvidenceList((prev) => [newEv, ...prev]);
      return;
    }

    try {
      const res = await liveSonarApi.captureSnapshot(sessionId, trackId);
      if (res.evidence) {
        setEvidenceList((prev) => [res.evidence, ...prev]);
      }
    } catch (err: any) {
      alert(`Snapshot failed: ${err.message || err}`);
    }
  };

  return (
    <div className="p-6 space-y-4 max-w-[1600px] mx-auto min-h-[calc(100vh-4rem)] flex flex-col">
      {/* Page Header */}
      <div className="flex flex-wrap items-center justify-between gap-4 pb-2 border-b border-border-subtle">
        <div className="space-y-0.5">
          <div className="flex items-center gap-2">
            <Radio className="w-5 h-5 text-accent animate-pulse" />
            <h1 className="text-xl font-bold text-text-primary font-sans tracking-tight">
              Live Sonar AI Detection & Tracking
            </h1>
          </div>
          <p className="text-text-muted text-xs">
            Real-time acoustic stream processing, YOLOv8 inference, ByteTrack temporal identity association, and forensic evidence capture.
          </p>
        </div>

        <div className="flex items-center gap-3 font-mono text-xs">
          {!isRunning || !isDemoMode ? (
            <button
              onClick={handleStartDemo}
              className="flex items-center gap-2 px-4 py-2 rounded-xl bg-accent text-white font-semibold text-xs hover:bg-accent-hover transition-all shadow-md active:scale-95 cursor-pointer"
            >
              <Play className="w-4 h-4 fill-current" />
              <span>🎬 Launch Live Detection Demo</span>
            </button>
          ) : (
            <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-purple-500/15 border border-purple-500/30 text-purple-900 font-semibold text-xs">
              <span className="w-2 h-2 rounded-full bg-purple-600 animate-ping" />
              <span>DEMO MODE ACTIVE</span>
            </div>
          )}

          <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-bg-surface border border-border-subtle">
            <Database className="w-3.5 h-3.5 text-text-muted" />
            <span className="text-text-muted">MODEL:</span>
            <span className="font-semibold text-text-primary">
              {health?.model_status === "LOADED" ? "YOLOv8-FLS (Active)" : "sonar_yolov8_fls"}
            </span>
          </div>
        </div>
      </div>

      {/* Active Demo Mode Status Banner */}
      {isDemoMode && isRunning && (
        <div className="flex items-center justify-between p-3.5 rounded-xl bg-purple-900/10 border border-purple-500/30 text-purple-950 font-mono text-xs shadow-sm">
          <div className="flex items-center gap-2.5">
            <Sparkles className="w-4 h-4 text-purple-700 animate-spin" />
            <span className="font-bold uppercase tracking-wider text-purple-800">🎬 Live Sonar Demo Active:</span>
            <span className="text-purple-900">
              Playing continuous ARIS 3000 forward-looking sonar with real-time YOLOv8 debris detection, ByteTrack object tracking, and acoustic shadow reasoning.
            </span>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={demoPlayer.step}
              className="px-2.5 py-1 rounded-lg bg-purple-100 hover:bg-purple-200 text-purple-900 border border-purple-300 text-[11px] font-semibold transition-all flex items-center gap-1 cursor-pointer"
            >
              <RefreshCw className="w-3 h-3" /> Step Frame
            </button>
            <button
              onClick={handleStopDemo}
              className="px-3 py-1 rounded-lg bg-purple-800 text-white hover:bg-purple-900 text-[11px] font-semibold transition-all shadow-sm flex items-center gap-1 cursor-pointer"
            >
              <StopCircle className="w-3 h-3" /> Stop Demo
            </button>
          </div>
        </div>
      )}

      {/* Stream Connection Config */}
      <ConnectionPanel
        currentConfig={sessionConfig}
        isRunning={isRunning}
        onStartSession={handleStartSession}
        onStopSession={handleStopSession}
        isOpen={isConfigOpen}
        onToggleOpen={setIsConfigOpen}
        connectionError={connectionError}
      />

      {/* Real-time Telemetry & Metrics Bar */}
      <LiveMetricsBar
        metrics={activeMetrics}
        gpuDevice={isDemoMode ? "GPU (ARIS 3K Telemetry)" : health?.inference_device || "CPU"}
      />

      {/* Main Sonar Viewport & Target Sidepanel */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-4 flex-1">
        {/* Sonar Viewport + Controls Deck (col-span-8) */}
        <div className="lg:col-span-8 flex flex-col gap-3">
          <div className="flex-1 min-h-[460px]">
            <LiveSonarCanvas
              frame={activeFrame}
              directImageElement={directImage}
              tracks={activeTracks}
              viewMode={viewMode}
              sourceType={isDemoMode ? "demo" : sessionConfig.source_type}
              connectionState={isDemoMode ? "CONNECTED" : connectionState}
              lastFrameTime={isDemoMode ? new Date() : lastFrameTime || new Date()}
              selectedTrackId={selectedTrackId}
              onSelectTrack={setSelectedTrackId}
              showTracks={showTracks}
              showTrails={showTrails}
              showShadows={showShadows}
              isRunning={isRunning}
              onOpenConfig={() => setIsConfigOpen(true)}
              onStartDemo={handleStartDemo}
            />
          </div>

          <ControlsDeck
            isPaused={isPaused}
            onTogglePause={handleTogglePause}
            isRecording={isRecording}
            onToggleRecord={handleToggleRecord}
            onCaptureSnapshot={() => handleCaptureSnapshot(selectedTrackId ?? undefined)}
            viewMode={viewMode}
            onChangeViewMode={setViewMode}
            sourceType={isDemoMode ? "replay" : sessionConfig.source_type}
            replaySpeed={replaySpeed}
            onChangeSpeed={handleSpeedChange}
            showTracks={showTracks}
            onToggleShowTracks={() => setShowTracks(!showTracks)}
            showTrails={showTrails}
            onToggleShowTrails={() => setShowTrails(!showTrails)}
            showShadows={showShadows}
            onToggleShowShadows={() => setShowShadows(!showShadows)}
          />
        </div>

        {/* Right Sidebar: Active Targets & Inspector (col-span-4) */}
        <div className="lg:col-span-4 flex flex-col">
          <ActiveTargetsPanel
            tracks={activeTracks}
            selectedTrackId={selectedTrackId}
            onSelectTrack={setSelectedTrackId}
            onCaptureSnapshot={handleCaptureSnapshot}
            evidenceList={evidenceList}
          />
        </div>
      </div>
    </div>
  );
};

export default LiveSonarPage;
