"""
Enhancement Profiles (Candidate Operational Hypotheses) & Pipeline Builders.

Implements Requirement R12:
1. RAW
2. MINIMAL
3. BALANCED
4. HUMAN_VISUAL
5. AI_SAFE
6. RESEARCH_CUSTOM
"""

from typing import Dict, Any, List, Optional
from enum import Enum
import numpy as np

from backend.enhancement.types import ProfileName, EnhancementMethod, EnhancementResult
from backend.enhancement.methods import apply_enhancement_method
from backend.enhancement.pipeline_base import (
    SonarEnhancementPipeline,
    ProcessingMode,
)
from backend.enhancement.stages.stripe_filter import StripeNoiseNotchStage
from backend.enhancement.stages.speckle_filter import SpeckleDenoisingStage
from backend.enhancement.stages.contrast_stage import AdaptiveContrastStage
from backend.enhancement.stages.shadow_diagnostics import AcousticShadowPreservationStage


class StandardProfile(str, Enum):
    RAW = "RAW"
    MINIMAL = "MINIMAL"
    BALANCED = "BALANCED"
    HUMAN_VISUAL = "HUMAN_VISUAL"
    AI_SAFE = "AI_SAFE"
    RESEARCH_CUSTOM = "RESEARCH_CUSTOM"


PROFILE_REGISTRY: Dict[str, Dict[str, Any]] = {
    StandardProfile.RAW.value: {
        "name": "Raw Acoustic Signal",
        "hypothesis": "Unmodified canonical acoustic array with zero radiometric alterations.",
        "target_condition": "Baseline scientific control and pure sensor playback.",
        "ai_safe": True,
        "human_display": True,
    },
    StandardProfile.MINIMAL.value: {
        "name": "Minimal Speckle Smoothing",
        "hypothesis": "Gentle Lee filter (k=3) suppressing speckle variance with minimal CLAHE (clip=1.2).",
        "target_condition": "Low-noise environments requiring conservative target boundary preservation.",
        "ai_safe": True,
        "human_display": True,
    },
    StandardProfile.BALANCED.value: {
        "name": "Balanced Acoustic Profile",
        "hypothesis": "Stripe notch evaluation, Lee multiplicative filter (k=5), CLAHE (clip=1.8), and shadow retention check.",
        "target_condition": "General operational patrol in typical coastal and estuary environments.",
        "ai_safe": True,
        "human_display": True,
    },
    StandardProfile.HUMAN_VISUAL.value: {
        "name": "Human Visual Inspection",
        "hypothesis": "Aggressive CLAHE dynamic equalization (clip=2.2), unsharp boost (amount=0.5), gamma 0.9 for maximum contrast.",
        "target_condition": "Human operator workstation inspection of faint targets and acoustic shadow depth.",
        "ai_safe": False,  # Not validated for detector due to unsharp halo artifacts
        "human_display": True,
    },
    StandardProfile.AI_SAFE.value: {
        "name": "AI-Safe Detector Profile",
        "hypothesis": "Conservative speckle suppression with strict shadow validation and zero over-sharpening.",
        "target_condition": "Downstream YOLOv8 object detector inference without regression risk.",
        "ai_safe": True,
        "human_display": True,
    },
    StandardProfile.RESEARCH_CUSTOM.value: {
        "name": "Research / Custom Config",
        "hypothesis": "User-configured parametric stage pipeline for controlled ablation studies.",
        "target_condition": "Algorithmic research and experimental benchmarking.",
        "ai_safe": False,
        "human_display": True,
    },
}


def build_pipeline_for_profile(
    profile_name: str,
    mode: ProcessingMode = ProcessingMode.AI_SAFE,
    custom_params: Optional[Dict[str, Any]] = None,
) -> SonarEnhancementPipeline:
    """
    Constructs a calibrated SonarEnhancementPipeline for given operational profile.
    """
    params = custom_params or {}
    p_name = profile_name.upper()
    pipeline = SonarEnhancementPipeline(name=f"Pipeline_{p_name}")

    if p_name == StandardProfile.RAW.value:
        return pipeline

    if p_name == StandardProfile.MINIMAL.value:
        pipeline.add_stage(SpeckleDenoisingStage(method="lee", window_size=3))
        pipeline.add_stage(AdaptiveContrastStage(clip_limit=1.2, tile_grid_size=(8, 8)))
        return pipeline

    if p_name == StandardProfile.BALANCED.value:
        pipeline.add_stage(StripeNoiseNotchStage(confidence_threshold=0.40))
        pipeline.add_stage(SpeckleDenoisingStage(method="lee", window_size=5))
        pipeline.add_stage(AdaptiveContrastStage(clip_limit=1.8, tile_grid_size=(8, 8)))
        pipeline.add_stage(AcousticShadowPreservationStage())
        return pipeline

    if p_name == StandardProfile.HUMAN_VISUAL.value:
        pipeline.add_stage(StripeNoiseNotchStage(confidence_threshold=0.35))
        pipeline.add_stage(SpeckleDenoisingStage(method="bilateral", window_size=5))
        pipeline.add_stage(
            AdaptiveContrastStage(
                clip_limit=2.2,
                tile_grid_size=(8, 8),
                gamma=0.9,
                unsharp_amount=0.5,
                unsharp_sigma=1.0,
            )
        )
        pipeline.add_stage(AcousticShadowPreservationStage())
        return pipeline

    if p_name == StandardProfile.AI_SAFE.value:
        pipeline.add_stage(StripeNoiseNotchStage(confidence_threshold=0.50))
        pipeline.add_stage(SpeckleDenoisingStage(method="lee", window_size=5))
        pipeline.add_stage(
            AdaptiveContrastStage(
                clip_limit=1.5,
                tile_grid_size=(8, 8),
                gamma=1.0,
                unsharp_amount=0.0,
            )
        )
        pipeline.add_stage(AcousticShadowPreservationStage())
        return pipeline

    if p_name == StandardProfile.RESEARCH_CUSTOM.value:
        if params.get("stripe_noise_filter", True):
            pipeline.add_stage(StripeNoiseNotchStage(confidence_threshold=params.get("stripe_confidence", 0.40)))
        
        denoise_m = params.get("denoising_method", "lee")
        pipeline.add_stage(SpeckleDenoisingStage(method=denoise_m, window_size=params.get("window_size", 5)))

        if params.get("clahe", True):
            pipeline.add_stage(
                AdaptiveContrastStage(
                    clip_limit=params.get("clahe_clip_limit", 1.8),
                    tile_grid_size=tuple(params.get("clahe_grid_size", (8, 8))),
                    gamma=params.get("gamma", 1.0),
                    unsharp_amount=params.get("unsharp_amount", 0.0),
                )
            )

        pipeline.add_stage(AcousticShadowPreservationStage())
        return pipeline

    # Fallback to Balanced
    return build_pipeline_for_profile(StandardProfile.BALANCED.value, mode=mode)


def list_profiles() -> List[Dict[str, Any]]:
    """Returns list of registered profiles with hypotheses and safety flags."""
    return [
        {
            "id": k,
            **v,
        }
        for k, v in PROFILE_REGISTRY.items()
    ]


def get_profile_info(profile_name: str) -> Optional[Dict[str, Any]]:
    return PROFILE_REGISTRY.get(profile_name.upper())


def apply_profile(arg1: Any, arg2: Any, **kwargs) -> EnhancementResult:
    """Legacy backward-compatible adapter handling both (profile, image) and (image, profile)."""
    if isinstance(arg1, (str, ProfileName, StandardProfile)):
        profile_name = arg1
        image = arg2
    else:
        image = arg1
        profile_name = arg2

    p_str = profile_name.value if hasattr(profile_name, "value") else str(profile_name)
    info = get_profile_info(p_str)
    if info and "primary_method" in info:
        res = apply_enhancement_method(info["primary_method"], image, **info.get("parameters", {}))
    elif p_str.upper() in ["BALANCED", "AI_SAFE"]:
        res = apply_enhancement_method(EnhancementMethod.CLAHE, image, clip_limit=1.8)
    elif p_str.upper() == "MINIMAL":
        res = apply_enhancement_method(EnhancementMethod.CLAHE, image, clip_limit=1.2)
    elif p_str.upper() == "HUMAN_VISUAL":
        res = apply_enhancement_method(EnhancementMethod.UNSHARP_CLAHE, image)
    else:
        res = apply_enhancement_method(EnhancementMethod.IDENTITY, image)

    try:
        res.profile_used = ProfileName[p_str.upper()]
    except (KeyError, ValueError):
        res.profile_used = ProfileName.BALANCED
    return res
