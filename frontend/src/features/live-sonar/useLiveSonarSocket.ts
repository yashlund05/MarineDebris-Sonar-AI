import { useEffect, useRef, useState, useCallback } from "react";
import { LiveFramePayload, LiveMetrics, LiveTrack, LiveDetection } from "./types";

export interface UseLiveSonarSocketOptions {
  sessionId?: string | null;
  autoConnect?: boolean;
  onFrame?: (payload: LiveFramePayload) => void;
  onError?: (error: any) => void;
}

export type ConnectionState = "DISCONNECTED" | "CONNECTING" | "CONNECTED" | "RECONNECTING" | "CONNECTION_LOST";

export function useLiveSonarSocket({
  sessionId,
  autoConnect = true,
  onFrame,
  onError,
}: UseLiveSonarSocketOptions) {
  const [connectionState, setConnectionState] = useState<ConnectionState>("DISCONNECTED");
  const [latestFrame, setLatestFrame] = useState<LiveFramePayload | null>(null);
  const [tracks, setTracks] = useState<LiveTrack[]>([]);
  const [detections, setDetections] = useState<LiveDetection[]>([]);
  const [metrics, setMetrics] = useState<LiveMetrics>({
    input_fps: 0,
    inference_fps: 0,
    display_fps: 0,
    latency_ms: 0,
    queue_depth: 0,
    frames_dropped: 0,
    drop_rate: 0,
    active_tracks: 0,
    confirmed_targets: 0,
  });
  const [lastFrameTime, setLastFrameTime] = useState<Date | null>(null);
  const [isPaused, setIsPaused] = useState<boolean>(false);

  const socketRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<any>(null);
  const reconnectAttemptsRef = useRef<number>(0);
  const isExplicitCloseRef = useRef<boolean>(false);

  // Local display FPS measurement
  const frameCountRef = useRef<number>(0);
  const lastFpsCalcTimeRef = useRef<number>(performance.now());
  const displayFpsRef = useRef<number>(0);

  const connect = useCallback(() => {
    if (!sessionId) return;

    if (socketRef.current) {
      isExplicitCloseRef.current = true;
      socketRef.current.close();
      socketRef.current = null;
    }

    isExplicitCloseRef.current = false;
    setConnectionState((prev) => (prev === "CONNECTED" ? "RECONNECTING" : "CONNECTING"));

    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const host = window.location.host;
    // Both /api/v1/ws/live-sonar and /ws/live-sonar are mounted on backend
    const wsUrl = `${protocol}//${host}/api/v1/ws/live-sonar/${sessionId}`;

    try {
      const ws = new WebSocket(wsUrl);
      socketRef.current = ws;

      ws.onopen = () => {
        setConnectionState("CONNECTED");
        reconnectAttemptsRef.current = 0;
      };

      ws.onmessage = (event) => {
        try {
          const payload = JSON.parse(event.data);

          if (payload.type === "frame_result") {
            const frame = payload as LiveFramePayload;
            setLatestFrame(frame);
            setTracks(frame.tracks || []);
            setDetections(frame.detections || []);
            setLastFrameTime(new Date());

            // Compute local display FPS
            frameCountRef.current += 1;
            const now = performance.now();
            const elapsed = now - lastFpsCalcTimeRef.current;
            if (elapsed >= 1000) {
              displayFpsRef.current = Math.round((frameCountRef.current * 1000) / elapsed);
              frameCountRef.current = 0;
              lastFpsCalcTimeRef.current = now;
            }

            setMetrics({
              ...frame.metrics,
              display_fps: displayFpsRef.current,
            });

            if (onFrame) {
              onFrame(frame);
            }
          } else if (payload.type === "command_ack") {
            if (payload.action === "pause") {
              setIsPaused(true);
            } else if (payload.action === "resume") {
              setIsPaused(false);
            }
          } else if (payload.type === "error") {
            console.error("Live Sonar WebSocket Error:", payload.message);
            if (onError) onError(payload.message);
          }
        } catch (err) {
          console.error("Failed to parse WebSocket JSON message:", err);
        }
      };

      ws.onerror = (err) => {
        console.error("Live Sonar WebSocket connection error:", err);
        if (onError) onError(err);
      };

      ws.onclose = () => {
        socketRef.current = null;
        if (!isExplicitCloseRef.current) {
          setConnectionState("CONNECTION_LOST");
          reconnectAttemptsRef.current += 1;
          const backoff = Math.min(1000 * Math.pow(1.5, reconnectAttemptsRef.current), 10000);
          reconnectTimeoutRef.current = setTimeout(() => {
            setConnectionState("RECONNECTING");
            connect();
          }, backoff);
        } else {
          setConnectionState("DISCONNECTED");
        }
      };
    } catch (err) {
      console.error("Failed to instantiate WebSocket:", err);
      setConnectionState("ERROR" as any);
      if (onError) onError(err);
    }
  }, [sessionId, onFrame, onError]);

  const disconnect = useCallback(() => {
    isExplicitCloseRef.current = true;
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }
    if (socketRef.current) {
      socketRef.current.close();
      socketRef.current = null;
    }
    setConnectionState("DISCONNECTED");
  }, []);

  const sendCommand = useCallback((cmd: Record<string, any>) => {
    if (socketRef.current && socketRef.current.readyState === WebSocket.OPEN) {
      socketRef.current.send(JSON.stringify(cmd));
    }
  }, []);

  const pause = useCallback(() => {
    sendCommand({ action: "pause" });
    setIsPaused(true);
  }, [sendCommand]);

  const resume = useCallback(() => {
    sendCommand({ action: "resume" });
    setIsPaused(false);
  }, [sendCommand]);

  const setSpeed = useCallback((speed: number) => {
    sendCommand({ action: "speed", value: speed });
  }, [sendCommand]);

  const requestSnapshot = useCallback((trackId?: number) => {
    sendCommand({ action: "snapshot", track_id: trackId });
  }, [sendCommand]);

  useEffect(() => {
    if (autoConnect && sessionId) {
      connect();
    }
    return () => {
      disconnect();
    };
  }, [sessionId, autoConnect, connect, disconnect]);

  return {
    connectionState,
    latestFrame,
    tracks,
    detections,
    metrics,
    lastFrameTime,
    isPaused,
    connect,
    disconnect,
    pause,
    resume,
    setSpeed,
    requestSnapshot,
  };
}
