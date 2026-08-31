/**
 * Shared TypeScript type definitions conforming strictly to DB_SCHEMA.md and API_SPEC.md.
 */

export type SurveyFileType = "xtf" | "jsf" | "png" | "tiff";
export type SurveyChannel = "port" | "starboard" | "both" | "unknown";
export type SurveyStatus =
  | "uploaded"
  | "queued"
  | "preprocessing"
  | "inferring"
  | "postprocessing"
  | "georeferencing"
  | "reporting"
  | "complete"
  | "failed";

export type JobStatus = "pending" | "running" | "complete" | "failed" | "cancelled";

export type DetectionClass =
  | "derelict_fishing_gear"
  | "general_marine_debris"
  | "shipwreck"
  | "pipe_or_cylinder"
  | "other_man_made_target"
  | "natural_feature";

export type ReportFormat = "json" | "csv" | "geojson";
export type ModelTask = "detection" | "segmentation" | "edge_detection";

export interface Survey {
  id: string;
  source_filename: string;
  storage_path: string;
  file_type: SurveyFileType;
  file_size_bytes: number;
  status: SurveyStatus;
  channel?: SurveyChannel;
  created_at: string;
  updated_at: string;
  processing_started_at?: string;
  processing_completed_at?: string;
  error_message?: string;
}

export interface SonarMetadata {
  id: string;
  survey_id: string;
  frequency_hz?: number;
  samples_per_ping?: number;
  total_pings?: number;
  range_resolution_m?: number;
  along_track_resolution_m?: number;
  min_latitude?: number;
  max_latitude?: number;
  min_longitude?: number;
  max_longitude?: number;
  survey_start_time?: number;
  survey_end_time?: number;
  sonar_system?: string;
  motion_quality_score?: number;
  dropout_pct?: number;
  has_attitude_data: boolean;
  raw_header?: Record<string, unknown>;
}

export interface ProcessingJob {
  id: string;
  survey_id: string;
  celery_task_id?: string;
  status: JobStatus;
  progress_pct: number;
  current_stage?: string;
  preprocessing_version?: string;
  detection_model?: string;
  detection_model_version?: string;
  segmentation_model?: string;
  detection_conf_threshold: number;
  nms_iou_threshold: number;
  tile_size: number;
  tile_overlap: number;
  created_at: string;
  updated_at: string;
}

export interface BoundingBox {
  x: number;
  y: number;
  w: number;
  h: number;
}

export interface Detection {
  id: string;
  survey_id: string;
  job_id: string;
  detection_code: string;
  class_name: DetectionClass;
  confidence: number;
  confidence_calibrated?: number;
  bbox_x: number;
  bbox_y: number;
  bbox_w: number;
  bbox_h: number;
  mask_rle?: string;
  estimated_length_m?: number;
  estimated_width_m?: number;
  geotagging_available: boolean;
  latitude?: number;
  longitude?: number;
  ping_number?: number;
  ping_timestamp?: number;
  is_filtered: boolean;
  filtered_reason?: string;
  source_tile_path?: string;
  extra_metadata?: Record<string, unknown>;
  created_at: string;
}

export interface Report {
  id: string;
  survey_id: string;
  job_id: string;
  format: ReportFormat;
  storage_path: string;
  file_size_bytes?: number;
  detection_count?: number;
  created_at: string;
}

export interface ModelRegistryItem {
  id: string;
  model_name: string;
  version: string;
  task: ModelTask;
  architecture?: string;
  training_dataset?: string;
  map50?: number;
  map50_95?: number;
  dice_score?: number;
  inference_latency_ms?: number;
  weight_path?: string;
  is_active: boolean;
  training_config?: Record<string, unknown>;
  trained_at?: string;
  registered_at: string;
}

export interface ApiResponse<T> {
  success: boolean;
  data: T;
  meta: {
    request_id: string;
    timestamp: string;
  };
}

export interface ApiErrorResponse {
  success: false;
  error: {
    code: string;
    message: string;
    details?: Record<string, unknown>;
  };
  meta: {
    request_id: string;
    timestamp: string;
  };
}

export interface SystemHealth {
  status: "ok" | "degraded" | "error";
  database: string;
  redis: string;
  worker: string;
  active_detection_model: string;
  device: string;
}
