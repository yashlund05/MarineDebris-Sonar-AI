export type LiveSourceType = "demo" | "replay" | "rtsp" | "usb" | "native_stub";
export type PreprocessingProfile = "REALTIME" | "BALANCED" | "QUALITY";
export type DropPolicy = "DROP_OLDEST" | "FIFO" | "DROP_NEWEST" | "LATEST";
export type ViewMode = "RAW" | "ENHANCED" | "AI" | "SPLIT";
export type SessionStatus = "IDLE" | "CONNECTING" | "CONNECTED" | "RUNNING" | "DEGRADED" | "STOPPING" | "STOPPED" | "ERROR" | "CONNECTION_LOST";

export interface BoundingBox {
  x: number;
  y: number;
  w: number;
  h: number;
}

export interface TrajectoryPoint {
  x: number;
  y: number;
}

export interface LiveTrack {
  track_id: number;
  class_name: string;
  class_id: number;
  confidence: number;
  bbox: BoundingBox;
  status: "TENTATIVE" | "CONFIRMED" | "LOST" | "DELETED";
  frames_seen: number;
  first_seen: string;
  last_seen: string;
  trajectory: TrajectoryPoint[];
  acoustic_shadow?: string | null;
  latitude?: number | null;
  longitude?: number | null;
  depth_m?: number | null;
}

export interface LiveDetection {
  class_id: number;
  class_name: string;
  confidence: number;
  bbox_x: number;
  bbox_y: number;
  bbox_w: number;
  bbox_h: number;
  acoustic_shadow?: string | null;
  latitude?: number | null;
  longitude?: number | null;
  depth_m?: number | null;
}

export interface LiveMetrics {
  input_fps: number;
  inference_fps: number;
  display_fps?: number;
  latency_ms: number;
  queue_depth: number;
  frames_dropped: number;
  drop_rate: number;
  active_tracks: number;
  confirmed_targets: number;
}

export interface SonarMetadata {
  frequency_hz?: number | null;
  range_m?: number | null;
  gain_db?: number | null;
}

export interface NavigationTelemetry {
  latitude?: number | null;
  longitude?: number | null;
  heading_deg?: number | null;
  depth_m?: number | null;
}

export interface LiveFramePayload {
  type: "frame_result";
  session_id: string;
  frame_id: string;
  sequence_number: number;
  timestamp_utc: string;
  preview_jpeg?: string | null;
  detections: LiveDetection[];
  tracks: LiveTrack[];
  metrics: LiveMetrics;
  sonar_metadata?: SonarMetadata;
  navigation?: NavigationTelemetry;
}

export interface LiveSessionConfig {
  session_id?: string;
  name: string;
  source_type: LiveSourceType;
  source_uri: string;
  target_fps: number;
  inference_fps: number;
  buffer_size: number;
  drop_policy: DropPolicy;
  preprocessing_profile: PreprocessingProfile;
  enable_tracking: boolean;
  enable_recording: boolean;
  confidence_threshold: number;
  minimum_confirmed_frames: number;
}

export interface LiveSessionDetails {
  session_id: string;
  name: string;
  source_type: string;
  source_uri: string;
  status: string;
  started_at?: string | null;
  stopped_at?: string | null;
  metrics?: Record<string, any> | null;
  is_recording: boolean;
  active_tracks_count: number;
  confirmed_targets_count: number;
}

export interface EvidenceRecord {
  evidence_id: string;
  session_id: string;
  track_id: number;
  frame_id: string;
  timestamp_utc: string;
  class_name: string;
  confidence: number;
  bbox: [number, number, number, number];
  raw_crop_path?: string;
  processed_crop_path?: string;
  annotated_crop_path?: string;
  metadata_json_path?: string;
  metadata?: Record<string, any>;
}

export interface LiveHealthStatus {
  status: string;
  active_sessions_count: number;
  gpu_available: boolean;
  inference_device: string;
  model_status: string;
  model_loaded: boolean;
  timestamp_utc: string;
}
