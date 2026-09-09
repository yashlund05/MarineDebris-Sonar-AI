/**
 * Types for SidescanTools Sonar Image Enhancement & Visualization.
 * Smart India Hackathon 2026 — PS26057.
 */

export interface QualityMetricDetails {
  mean_intensity: number;
  std_intensity: number;
  dynamic_range: number;
  rms_contrast: number;
  entropy: number;
  edge_density: number;
  brenner_gradient: number;
  tenengrad: number;
  enl_diagnostic?: number | null;
}

export interface ComparativeMetrics {
  raw: QualityMetricDetails;
  enhanced: QualityMetricDetails;
  delta: {
    contrast_gain: number;
    entropy_delta: number;
    dynamic_range_gain: number;
    sharpness_ratio: number;
  };
}

export interface DetectionBox {
  class_name: string;
  confidence: number;
  bbox: [number, number, number, number]; // [x, y, w, h]
}

export interface DetectionResults {
  mode: string;
  conf_threshold: number;
  detection_count: number;
  detections: DetectionBox[];
  inference_time_ms: number;
}

export interface SonarEnhancementConfig {
  convert_to_db: boolean;
  stripe_noise_filter: boolean;
  clahe: boolean;
  clahe_clip_limit: number;
  clahe_grid_size?: [number, number];
  sharpening: boolean;
  sharpening_gamma_h: number;
  sharpening_gamma_l: number;
  sharpening_c: number;
  gain_normalization: boolean;
  colormap: string;
  run_detection: boolean;
  conf_threshold: number;
  detection_input_mode: "enhanced_grayscale" | "raw";
}

export interface EnhancementResponse {
  success: boolean;
  cache_key: string;
  cache_hit: boolean;
  pipeline_version: string;
  source_filename: string;
  raw_sha256: string;
  execution_time_ms: number;
  raw_image_data_url: string;
  enhanced_grayscale_data_url: string;
  pseudocolor_data_url: string;
  colormap: string;
  metrics: ComparativeMetrics;
  audit_trail: string[];
  applied_operations: string[];
  input_representation: {
    type: string;
    shape: number[];
    dtype: string;
    min_val: number;
    max_val: number;
    db_applicable: boolean;
  };
  config_applied: Record<string, any>;
  detection_results?: DetectionResults | null;
}

export interface PaletteItem {
  id: string;
  name: string;
  description: string;
  is_default: boolean;
}

export interface SampleItem {
  name: string;
  has_annotations: boolean;
  box_count: number;
}
