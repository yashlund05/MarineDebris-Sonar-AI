export type ConfidenceState = "VERIFIED" | "DERIVED" | "DECLARED" | "NOT_AVAILABLE" | "CONFLICT";

export interface Confident<T> {
  data: T | null;
  confidence: ConfidenceState;
}

export interface DatasetVersion {
  version_id: string;
  name: string;
  status: "FROZEN_READY" | "LEGACY" | "DEVELOPMENT" | string;
  release_date?: string;
}

export interface OverviewData {
  total_images?: number;
  total_annotations?: number;
  total_sequences?: number;
  total_positives?: number;
  total_negatives?: number;
  status_badge?: string;
  integrity_statement?: string;
}

export interface SourceAccounting {
  source_name: string;
  real_images: number;
  positives: number;
  negatives: number;
  boxes: number;
  sequences: number;
  modality: string;
  sensor: string;
  peer_review_status: string;
  doi?: string;
}

export interface SplitStats {
  train: { images: number; annotations: number; negatives: number };
  val: { images: number; annotations: number; negatives: number };
  test: { images: number; annotations: number; negatives: number };
}

export interface ClassDistribution {
  class_name: string;
  count: number;
  is_canonical: boolean;
}

export interface ScaleDistribution {
  scale: "Tiny" | "Small" | "Medium" | "Large" | string;
  count: number;
  definition: string;
}

export interface SensorProfile {
  sonar_camera: string;
  frequency: string;
  institution: string;
  pi: string;
  doi?: string;
  license: string;
  modality?: string;
  primary_environment?: string;
  additional_negative_domain?: string;
  core_data_type?: string;
  synthetic_auxiliary?: string;
  canonical_taxonomy_coverage?: string;
}

export interface TaxonomyClass {
  id: string;
  name: string;
  description: string;
}

export interface SourceClassMapping {
  source_class: string;
  mapped_canonical: string;
}

export interface TaxonomyData {
  canonical_classes: TaxonomyClass[];
  source_mapping: SourceClassMapping[];
}

export interface ProvenanceData {
  source_name: string;
  institutions: string[];
  publications: string[];
  dois: string[];
  licenses: string[];
}

export interface IntegrityData {
  leakage_status: string;
  dedup_accounting: string;
  annotation_errors: string;
}

export interface HardNegativeData {
  total_verified_negatives: number;
  breakdown: Record<string, number>;
  far_statistics?: string;
}

export interface BenchmarkMetrics {
  mAP50: number;
  recall: number;
  precision: number;
  f1: number;
  mAP50_95: number;
  test_images: number;
  test_objects: number;
}

export interface BenchmarkData {
  type: "CANONICAL" | "OPERATIONAL" | string;
  confidence_threshold: number;
  iou_threshold: number;
  metrics: BenchmarkMetrics;
}

export interface VariantInfo {
  variant_id: string;
  description: string;
}

export interface LineageData {
  nodes: { id: string; label: string; count_images?: number; count_annotations?: number }[];
  edges: { from: string; to: string; label: string }[];
}

export interface LimitationData {
  unrepresented_classes: string[];
  single_sensor: string;
  controlled_environment: string;
  generalization_note: string;
}

export interface CanonicalClassAudit {
  class_id: number;
  class_name: string;
  description: string;
  benchmark_status: "ESTABLISHED" | "PROVISIONAL" | "INSUFFICIENT_DATA" | "NOT_FOUND" | "RESTRICTED" | string;
  model_status: string;
  sample_count: number;
  sensor: string;
  modality: string;
  source_dataset: string;
  license: string;
  secondary_source?: string;
  ap50: number;
  operational_recall: number;
  recommendation: string;
}

export interface CanonicalAuditData {
  timestamp: string;
  production_model: Record<string, any>;
  canonical_classes: CanonicalClassAudit[];
  benchmark_5_summary?: Record<string, any>;
}

export interface DatasetSummary {
  version_id: string;
  overview: Confident<OverviewData>;
  source_level_accounting: Confident<SourceAccounting[]>;
  splits: Confident<SplitStats>;
  class_distribution: Confident<ClassDistribution[]>;
  scale_distribution: Confident<ScaleDistribution[]>;
  sensor: Confident<SensorProfile>;
  taxonomy: Confident<TaxonomyData>;
  provenance: Confident<ProvenanceData[]>;
  integrity: Confident<IntegrityData>;
  hard_negatives: Confident<HardNegativeData>;
  benchmarks: Confident<BenchmarkData[]>;
  variants: Confident<VariantInfo[]>;
  lineage: Confident<LineageData>;
  limitations: Confident<LimitationData>;
  canonical_audit?: Confident<CanonicalAuditData>;
}

