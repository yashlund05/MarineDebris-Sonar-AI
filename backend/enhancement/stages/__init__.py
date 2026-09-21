"""
Modular processing stages for the Sonar Enhancement Pipeline.
"""

from .stripe_filter import StripeNoiseNotchStage
from .speckle_filter import SpeckleDenoisingStage, lee_filter, frost_filter, srad_filter
from .shadow_diagnostics import AcousticShadowPreservationStage
from .contrast_stage import AdaptiveContrastStage

__all__ = [
    "StripeNoiseNotchStage",
    "SpeckleDenoisingStage",
    "lee_filter",
    "frost_filter",
    "srad_filter",
    "AcousticShadowPreservationStage",
    "AdaptiveContrastStage",
]
