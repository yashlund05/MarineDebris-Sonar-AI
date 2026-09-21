import { useState, useEffect, useRef, useCallback } from "react";
import { DEMO_SONAR_FRAMES } from "./demoData";
import { LiveFramePayload } from "./types";

export interface UseDemoPlayerOptions {
  enabled?: boolean;
  speed?: number;
}

export function useDemoPlayer({ enabled = true, speed = 1.0 }: UseDemoPlayerOptions = {}) {
  const [frameIndex, setFrameIndex] = useState<number>(0);
  const [isPlaying, setIsPlaying] = useState<boolean>(true);
  const [imagesLoaded, setImagesLoaded] = useState<boolean>(false);
  const [displayFps, setDisplayFps] = useState<number>(15);

  const imagesRef = useRef<HTMLImageElement[]>([]);
  const frameCountRef = useRef<number>(0);
  const lastFpsCalcRef = useRef<number>(performance.now());
  const intervalRef = useRef<any>(null);
  const seqRef = useRef<number>(1);

  // Preload authentic sonar frames into memory
  useEffect(() => {
    let loadedCount = 0;
    const loadedImgs: HTMLImageElement[] = [];

    DEMO_SONAR_FRAMES.forEach((frameDef, idx) => {
      const img = new Image();
      img.src = frameDef.imageSrc;
      img.onload = () => {
        loadedCount++;
        if (loadedCount === DEMO_SONAR_FRAMES.length) {
          setImagesLoaded(true);
        }
      };
      img.onerror = () => {
        console.warn(`Failed to preload demo frame: ${frameDef.imageSrc}`);
      };
      loadedImgs[idx] = img;
    });

    imagesRef.current = loadedImgs;
  }, []);

  // Frame advancing loop
  useEffect(() => {
    if (!enabled || !isPlaying) {
      if (intervalRef.current) clearInterval(intervalRef.current);
      return;
    }

    const intervalMs = Math.max(20, Math.round(1000 / (1.5 * speed))); // ~1.5 - 2 seconds per frame sequence or smoothly stepping
    intervalRef.current = setInterval(() => {
      setFrameIndex((prev) => (prev + 1) % DEMO_SONAR_FRAMES.length);
      seqRef.current += 1;

      // Measure local rendering FPS
      frameCountRef.current += 1;
      const now = performance.now();
      const dt = now - lastFpsCalcRef.current;
      if (dt >= 1000) {
        setDisplayFps(Math.round((frameCountRef.current * 1000) / dt));
        frameCountRef.current = 0;
        lastFpsCalcRef.current = now;
      }
    }, intervalMs);

    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, [enabled, isPlaying, speed]);

  const currentDef = DEMO_SONAR_FRAMES[frameIndex];
  const currentImage = imagesRef.current[frameIndex] || null;

  // Build live frame payload format matching backend WebSocket
  const liveFramePayload: LiveFramePayload = {
    type: "frame_result",
    session_id: "demo_session_fls",
    frame_id: `demo_frame_${seqRef.current}`,
    sequence_number: seqRef.current,
    timestamp_utc: new Date().toISOString(),
    preview_jpeg: null,
    detections: currentDef.detections,
    tracks: currentDef.tracks,
    metrics: {
      input_fps: Number((15.0 * speed).toFixed(1)),
      inference_fps: Number((10.0 * Math.min(1.5, speed)).toFixed(1)),
      display_fps: displayFps || 15,
      latency_ms: 38.4,
      queue_depth: 2,
      frames_dropped: 0,
      drop_rate: 0,
      active_tracks: currentDef.tracks.length,
      confirmed_targets: currentDef.tracks.filter((t) => t.status === "CONFIRMED").length,
    },
    sonar_metadata: currentDef.sonar_metadata,
    navigation: currentDef.navigation,
  };

  const play = useCallback(() => setIsPlaying(true), []);
  const pause = useCallback(() => setIsPlaying(false), []);
  const togglePlay = useCallback(() => setIsPlaying((p) => !p), []);
  const step = useCallback(() => {
    setFrameIndex((prev) => (prev + 1) % DEMO_SONAR_FRAMES.length);
    seqRef.current += 1;
  }, []);

  return {
    currentDef,
    currentImage,
    currentFramePayload: liveFramePayload,
    imagesLoaded,
    isPlaying,
    play,
    pause,
    togglePlay,
    step,
    frameIndex,
    totalFrames: DEMO_SONAR_FRAMES.length,
  };
}
