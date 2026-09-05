export interface MetricEntry {
  precision?: number | null;
  recall?: number | null;
  f1?: number | null;
  map50?: number | null;
  map50_95?: number | null;
  far?: number | null;
  fnr?: number | null;
  false_positive_count?: number | null;
  false_negative_count?: number | null;
  latency_mean_ms?: number | null;
  latency_p50_ms?: number | null;
  latency_p95_ms?: number | null;
  latency_p99_ms?: number | null;
  throughput?: number | null;
  confidence_threshold?: number | null;
  iou_threshold?: number | null;
  evaluation_split?: string | null;
  dataset_version?: string | null;
}

export interface ModelMetricsResponse {
  model_id: string;
  display_name: string;
  confidence: 'VERIFIED' | 'DERIVED' | 'DECLARED' | 'NOT_AVAILABLE' | 'CONFLICT';
  is_measured: boolean;
  metrics: {
    canonical_benchmark?: MetricEntry | null;
    operational_point?: MetricEntry | null;
    hard_negatives?: MetricEntry | null;
    latency_profile?: MetricEntry | null;
  };
  provenance?: {
    evaluated_at?: string;
    evaluator?: string;
    source_artifacts?: string[];
  };
}

export interface PromotionGateCheck {
  name: string;
  required: string;
  observed: string;
  passed: boolean;
}

export interface PromotionGateResult {
  status: 'REJECTED' | 'ELIGIBLE_FOR_PROMOTION' | 'NOT_EVALUATED' | string;
  overall_pass: boolean;
  promotion_eligible: boolean;
  checks: PromotionGateCheck[];
  recommendation?: string | null;
}

export interface PromotionDecisionResponse {
  model_id: string;
  is_production: boolean;
  promotion_gate?: PromotionGateResult | null;
  status: string;
  rationale?: string;
}

export interface MultiSeedStats {
  mean: number;
  std: number;
  min: number;
  max: number;
  values: number[];
  ci_95?: number[] | null;
  sample_size_note?: string | null;
}

export interface MultiSeedAggregation {
  seeds: number[];
  number_of_seeds: number;
  v2_mAP50: MultiSeedStats;
  v2_recall: MultiSeedStats;
  v3_mAP50: MultiSeedStats;
  v3_recall: MultiSeedStats;
  hard_negatives_FAR: MultiSeedStats;
  total_false_positive_boxes: MultiSeedStats;
  stability_passed: boolean;
  best_seed: number;
  best_checkpoint: string;
}

export interface MultiSeedRunsResponse {
  model_id: string;
  multiseed: {
    confidence: string;
    aggregation?: MultiSeedAggregation | null;
    individual_runs?: Array<{
      seed: number;
      experiment_id: string;
      checkpoint_path: string;
      metrics: Record<string, any>;
    }>;
  };
}

export interface ModelArtifactItem {
  type: string;
  path: string;
  exists: boolean;
  sha256?: string | null;
  size_bytes?: number | null;
  description?: string;
}

export interface ModelArtifactsResponse {
  model_id: string;
  artifacts: ModelArtifactItem[];
}

export interface ModelExplanationResponse {
  model_id: string;
  decision: string;
  rationale: string;
  strengths: string[];
  weaknesses: string[];
}

export interface RegisteredModelSummary {
  id: string;
  model_name: string;
  name: string;
  version: string;
  task: "detection" | "segmentation" | "edge_detection" | "classification" | string;
  architecture?: string;
  framework?: string;
  training_dataset?: string;
  dataset_version?: string;
  supported_classes?: string[];
  unsupported_classes?: string[];
  map50?: number | null;
  map50_95?: number | null;
  dice_score?: number | null;
  inference_latency_ms?: number | null;
  weight_path?: string;
  weights_path?: string;
  runtime_status?: string;
  status: string;
  device?: string;
  is_loaded?: boolean;
  is_active: boolean;
  metrics?: Record<string, any>;
  trained_at?: string | null;
  registered_at?: string | null;
}
