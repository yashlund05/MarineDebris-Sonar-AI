"""
MarineDebris-Sonar-AI: Dataset Engineering and V3 Pipeline Package
Provides modular dataset acquisition, provenance recording, format normalization,
annotation auditing, perceptual deduplication, sequence-aware splitting,
and reproducible dataset manifest generation.
"""

from .provenance import ProvenanceManager, ProvenanceRecord
from .normalize import ImageNormalizer
from .audit import AnnotationAuditor
from .deduplicate import DatasetDeduplicator
from .split import SequenceAwareSplitter

__all__ = [
    "ProvenanceManager",
    "ProvenanceRecord",
    "ImageNormalizer",
    "AnnotationAuditor",
    "DatasetDeduplicator",
    "SequenceAwareSplitter",
]
