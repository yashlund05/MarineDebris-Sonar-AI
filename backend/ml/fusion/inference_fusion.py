"""Inference decision fusion between detector and secondary classifier."""

from dataclasses import dataclass
from typing import Optional, Dict, Any

from backend.ml.classifier.base import ClassificationResult


@dataclass
class FusedDetectionResult:
    final_class_name: str
    confidence: float
    classification_status: str  # 'available', 'unavailable', 'disagreement'
    classifier_model: Optional[str] = None
    classifier_class: Optional[str] = None
    classifier_confidence: Optional[float] = None
    classification_agreement: Optional[bool] = None
    override_applied: bool = False


class InferenceFusion:
    """Combines YOLO detection with optional secondary classification."""

    @staticmethod
    def fuse(
        detector_class: str,
        detector_confidence: float,
        classification_result: ClassificationResult,
        classifier_name: Optional[str] = None,
        allow_override: bool = False,
    ) -> FusedDetectionResult:
        """Evaluate agreement between detector and classifier.
        
        Preserves YOLO detection as ground truth by default (allow_override=False).
        """
        if classification_result.status != "available":
            return FusedDetectionResult(
                final_class_name=detector_class,
                confidence=detector_confidence,
                classification_status="unavailable",
                classifier_model=classifier_name,
                classifier_class=None,
                classifier_confidence=None,
                classification_agreement=None,
                override_applied=False,
            )

        agreement = detector_class.lower() == (classification_result.class_name or "").lower()

        # If override is explicitly authorized and classifier is significantly more confident
        override_applied = False
        final_class = detector_class
        if (
            allow_override
            and not agreement
            and classification_result.confidence
            and classification_result.confidence > detector_confidence + 0.20
        ):
            final_class = classification_result.class_name
            override_applied = True

        return FusedDetectionResult(
            final_class_name=final_class,
            confidence=detector_confidence,
            classification_status="available",
            classifier_model=classifier_name,
            classifier_class=classification_result.class_name,
            classifier_confidence=classification_result.confidence,
            classification_agreement=agreement,
            override_applied=override_applied,
        )
