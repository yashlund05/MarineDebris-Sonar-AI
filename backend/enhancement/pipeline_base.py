"""
Core architectural abstractions for the Sonar Enhancement Subsystem.

Defines the common stage interface, pipeline orchestration, execution context,
and provenance tracking structures following Requirement R5.
"""

from __future__ import annotations

import time
import abc
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any, Tuple
import numpy as np


class Modality(str, Enum):
    FLS = "FLS"  # Forward-Looking Sonar (acoustic camera: ARIS, BlueView)
    SSS = "SSS"  # Side-Scan Sonar (towfish / hull-mounted)
    UNKNOWN = "UNKNOWN"


class SignalRepresentation(str, Enum):
    LINEAR_AMPLITUDE = "LINEAR_AMPLITUDE"
    LINEAR_INTENSITY = "LINEAR_INTENSITY"  # Amplitude squared
    DECIBEL = "DECIBEL"  # Logarithmic power/amplitude
    NORMALIZED_FLOAT = "NORMALIZED_FLOAT"  # Canonical float32 in [0.0, 1.0]
    DISPLAY_GRAYSCALE = "DISPLAY_GRAYSCALE"  # uint8 [0, 255]
    UNKNOWN = "UNKNOWN"


class ProcessingMode(str, Enum):
    HUMAN_DISPLAY = "HUMAN_DISPLAY"  # Maximum visual interpretability
    AI_SAFE = "AI_SAFE"  # Structure-preserving, zero-hallucination, YOLO-safe


@dataclass
class SonarEnhancementProvenance:
    """Provenance and audit metadata for reproducibility and compliance."""
    source_artifact_id: str
    modality: Modality
    input_representation: SignalRepresentation
    output_representation: SignalRepresentation
    applied_stages: List[str] = field(default_factory=list)
    skipped_stages: List[str] = field(default_factory=list)
    parameters_snapshot: Dict[str, Any] = field(default_factory=dict)
    execution_time_ms: float = 0.0
    device: str = "cpu"
    git_commit: Optional[str] = None
    software_version: str = "1.0.0"
    model_metadata: Optional[Dict[str, Any]] = None
    timestamp_utc: str = ""


@dataclass
class SonarEnhancementContext:
    """Execution context passed through every pipeline stage."""
    artifact_id: str
    modality: Modality = Modality.FLS
    representation: SignalRepresentation = SignalRepresentation.NORMALIZED_FLOAT
    mode: ProcessingMode = ProcessingMode.AI_SAFE
    validity_mask: Optional[np.ndarray] = None  # bool: True where acoustic data is valid
    confidence_mask: Optional[np.ndarray] = None  # float32 in [0, 1]
    modified_mask: Optional[np.ndarray] = None  # bool: True where pixels were altered
    metadata: Dict[str, Any] = field(default_factory=dict)
    warnings: List[str] = field(default_factory=list)
    stage_metrics: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    provenance: SonarEnhancementProvenance = field(
        default_factory=lambda: SonarEnhancementProvenance(
            source_artifact_id="",
            modality=Modality.UNKNOWN,
            input_representation=SignalRepresentation.UNKNOWN,
            output_representation=SignalRepresentation.UNKNOWN,
        )
    )


@dataclass
class SonarEnhancementResult:
    """Standardized result returned by a stage or pipeline."""
    canonical_image: np.ndarray  # 2D float32 [0.0, 1.0]
    display_image: Optional[np.ndarray] = None  # 8-bit RGB or grayscale for operator
    validity_mask: Optional[np.ndarray] = None
    confidence_mask: Optional[np.ndarray] = None
    modified_mask: Optional[np.ndarray] = None
    applied_stages: List[str] = field(default_factory=list)
    skipped_stages: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)
    execution_time_ms: float = 0.0
    is_ai_safe: bool = True
    provenance: Optional[SonarEnhancementProvenance] = None

    def __post_init__(self):
        if self.canonical_image is not None and self.canonical_image.size > 0:
            if self.canonical_image.ndim != 2:
                raise ValueError(f"Canonical image must be 2D single-channel, got shape {self.canonical_image.shape}")
            if self.canonical_image.dtype != np.float32:
                self.canonical_image = self.canonical_image.astype(np.float32)


class SonarEnhancementStage(abc.ABC):
    """Abstract base class for all modular enhancement stages."""

    def __init__(self, name: str, is_ai_safe_default: bool = True):
        self.name = name
        self._is_ai_safe_default = is_ai_safe_default

    @abc.abstractmethod
    def validate_input(self, image: np.ndarray, context: SonarEnhancementContext) -> bool:
        """Validates image dimensions, types, and context prerequisites."""
        pass

    @abc.abstractmethod
    def process(
        self, image: np.ndarray, context: SonarEnhancementContext
    ) -> Tuple[np.ndarray, Dict[str, Any]]:
        """
        Executes enhancement transformation.
        Returns:
            Tuple of (transformed_image, metrics_dict)
        """
        pass

    def validate_output(self, image: np.ndarray, context: SonarEnhancementContext) -> bool:
        """Validates that output satisfies canonical requirements."""
        if image is None or image.size == 0:
            return False
        if image.ndim != 2:
            return False
        if not np.all(np.isfinite(image)):
            return False
        return True

    def collect_metrics(
        self, original: np.ndarray, enhanced: np.ndarray, context: SonarEnhancementContext
    ) -> Dict[str, Any]:
        """Calculates stage-specific metrics."""
        return {}

    def supports_modality(self, modality: Modality) -> bool:
        """Declares whether this stage supports FLS, SSS, or both."""
        return True

    def supports_representation(self, representation: SignalRepresentation) -> bool:
        """Declares whether this stage can ingest given signal domain."""
        return representation in [
            SignalRepresentation.NORMALIZED_FLOAT,
            SignalRepresentation.LINEAR_AMPLITUDE,
            SignalRepresentation.DECIBEL,
        ]

    def is_ai_safe(self, context: SonarEnhancementContext) -> bool:
        """Whether stage preserves boundaries and shadows safely for detector."""
        return self._is_ai_safe_default

    def estimate_runtime_ms(self, shape: Tuple[int, ...]) -> float:
        """Estimates execution time for resource scheduling."""
        pixels = shape[0] * shape[1] if len(shape) >= 2 else 0
        return (pixels / (640 * 640)) * 5.0


class SonarEnhancementPipeline:
    """Configurable, composable multi-stage pipeline."""

    def __init__(self, name: str = "SonarEnhancementPipeline"):
        self.name = name
        self.stages: List[SonarEnhancementStage] = []

    def add_stage(self, stage: SonarEnhancementStage) -> SonarEnhancementPipeline:
        self.stages.append(stage)
        return self

    def execute(
        self, input_image: np.ndarray, context: SonarEnhancementContext
    ) -> SonarEnhancementResult:
        """
        Executes sequential pipeline stages with error isolation and mask propagation.
        """
        t0 = time.perf_counter()
        current_image = input_image.copy().astype(np.float32)
        applied_stages: List[str] = []
        skipped_stages: List[str] = []
        collected_metrics: Dict[str, Any] = {}

        # Initialize masks if missing
        if context.validity_mask is None:
            context.validity_mask = np.isfinite(current_image)
        if context.modified_mask is None:
            context.modified_mask = np.zeros_like(current_image, dtype=bool)

        for stage in self.stages:
            stage_name = stage.name
            # Modality check
            if not stage.supports_modality(context.modality):
                skipped_stages.append(f"{stage_name}:unsupported_modality")
                continue

            # Representation check
            if not stage.supports_representation(context.representation):
                skipped_stages.append(f"{stage_name}:unsupported_representation")
                continue

            # AI-Safe gating: if running in AI_SAFE mode, reject non-AI-safe stages
            if context.mode == ProcessingMode.AI_SAFE and not stage.is_ai_safe(context):
                skipped_stages.append(f"{stage_name}:not_ai_safe")
                continue

            # Input validation
            if not stage.validate_input(current_image, context):
                skipped_stages.append(f"{stage_name}:input_invalid")
                context.warnings.append(f"Stage '{stage_name}' rejected input array.")
                continue

            # Process stage with timing & safety barrier
            try:
                st_t0 = time.perf_counter()
                orig_stage_input = current_image.copy()
                transformed, st_metrics = stage.process(current_image, context)
                st_dt = (time.perf_counter() - st_t0) * 1000.0

                # Validate output
                if not stage.validate_output(transformed, context):
                    context.warnings.append(f"Stage '{stage_name}' produced invalid output. Reverting.")
                    skipped_stages.append(f"{stage_name}:output_invalid")
                    continue

                # Update modified mask where difference is non-trivial
                diff = np.abs(transformed - orig_stage_input) > 1e-4
                context.modified_mask = np.logical_or(context.modified_mask, diff)

                current_image = transformed
                applied_stages.append(stage_name)
                st_metrics["runtime_ms"] = round(st_dt, 3)
                collected_metrics[stage_name] = st_metrics
                context.stage_metrics[stage_name] = st_metrics

            except Exception as ex:
                context.warnings.append(f"Stage '{stage_name}' raised error: {str(ex)}. Skipped.")
                skipped_stages.append(f"{stage_name}:exception_{type(ex).__name__}")

        total_dt = (time.perf_counter() - t0) * 1000.0

        # Update context provenance
        context.provenance.applied_stages = applied_stages
        context.provenance.skipped_stages = skipped_stages
        context.provenance.execution_time_ms = round(total_dt, 3)

        return SonarEnhancementResult(
            canonical_image=np.clip(current_image, 0.0, 1.0),
            validity_mask=context.validity_mask,
            confidence_mask=context.confidence_mask,
            modified_mask=context.modified_mask,
            applied_stages=applied_stages,
            skipped_stages=skipped_stages,
            warnings=context.warnings,
            metrics=collected_metrics,
            execution_time_ms=round(total_dt, 3),
            is_ai_safe=(context.mode == ProcessingMode.AI_SAFE),
            provenance=context.provenance,
        )

    # Method alias for API consistency
    process = execute
