"""
Enhancement Profiles (Candidate Hypotheses).

METHODOLOGY DISCLOSURE:
Profiles defined here are candidate operational hypotheses designed for specific acoustic
imaging regimes. They are NOT assumed to be absolute physical truths; each profile must be
empirically validated against the benchmark suite and detection utility gates.
"""

from typing import Dict, Any, List
from backend.enhancement.types import ProfileName, EnhancementMethod, EnhancementResult
from backend.enhancement.methods import apply_enhancement_method
import numpy as np


PROFILE_REGISTRY: Dict[ProfileName, Dict[str, Any]] = {
    ProfileName.BALANCED: {
        "name": "Balanced Acoustic Inspection",
        "primary_method": EnhancementMethod.BILATERAL_CLAHE,
        "hypothesis": "Bilateral filtering (d=5, sigma_color=0.1, sigma_space=3) smooths seabed speckle while preserving target boundaries; subsequent CLAHE (clip=1.8) expands contrast without amplifying noise.",
        "target_condition": "General-purpose FLS operations in typical coastal/estuary environments.",
        "parameters": {
            "d": 5,
            "sigma_color": 0.1,
            "sigma_space": 3.0,
            "clip_limit": 1.8,
            "tile_grid_size": (8, 8)
        }
    },
    ProfileName.LOW_SNR: {
        "name": "Low-SNR / Homomorphic Bilateral",
        "primary_method": EnhancementMethod.LOG_BILATERAL_CLAHE,
        "hypothesis": "Transforming multiplicative acoustic speckle into additive noise in the log domain allows superior speckle suppression without obliterating faint target shadows in turbid water.",
        "target_condition": "Highly turbid water, high acoustic reverberation, weak return signatures.",
        "parameters": {
            "d": 5,
            "sigma_color": 0.15,
            "sigma_space": 3.0,
            "clip_limit": 1.6,
            "tile_grid_size": (8, 8)
        }
    },
    ProfileName.HIGH_CONTRAST: {
        "name": "High-Contrast Edge Boost",
        "primary_method": EnhancementMethod.UNSHARP_CLAHE,
        "hypothesis": "Gaussian unsharp masking (amount=0.6) boosts high-frequency acoustic reflections from hard metallic/synthetic debris edges, making geometric contours prominent.",
        "target_condition": "Cylindrical pipes, shipwreck hulls, man-made debris with sharp boundaries.",
        "parameters": {
            "sigma": 1.0,
            "amount": 0.6,
            "clip_limit": 2.0,
            "tile_grid_size": (8, 8)
        }
    },
    ProfileName.HEAVY_CLUTTER: {
        "name": "Heavy Clutter Suppression",
        "primary_method": EnhancementMethod.MEDIAN_CLAHE,
        "hypothesis": "Median filtering (k=5) suppresses impulsive acoustic multipath and scattered rock clutter before CLAHE equalization.",
        "target_condition": "Quarry walls, rock reefs, high-energy acoustic multipath environments.",
        "parameters": {
            "kernel_size": 5,
            "clip_limit": 1.8,
            "tile_grid_size": (8, 8)
        }
    },
    ProfileName.LONG_RANGE: {
        "name": "Long-Range Attenuation Compensation",
        "primary_method": EnhancementMethod.GAMMA_CORRECT,
        "hypothesis": "Power-law scaling (gamma=0.6) partially compensates for two-way acoustic transmission loss in the far field where return energy is low.",
        "target_condition": "Far-field targets (>10m range on ARIS 3000), darker distant acoustic sweeps.",
        "parameters": {
            "gamma": 0.6
        }
    },
    ProfileName.HUMAN_INSPECTION: {
        "name": "Human Operator Inspection",
        "primary_method": EnhancementMethod.BILATERAL_CLAHE,
        "hypothesis": "Combines edge-preserving bilateral filtering with moderate CLAHE tailored for maximum human eye differentiability when mapped to the ARIS Amber palette.",
        "target_condition": "Real-time workstation display during active survey operations.",
        "parameters": {
            "d": 5,
            "sigma_color": 0.08,
            "sigma_space": 2.5,
            "clip_limit": 2.2,
            "tile_grid_size": (8, 8)
        }
    },
    ProfileName.DETECTION_OPTIMIZED: {
        "name": "Detector Utility Candidate",
        "primary_method": EnhancementMethod.CLAHE,
        "hypothesis": "Standard CLAHE (clip=2.0, grid=8x8) aligns directly with the preprocessing used during YOLOv8 training, minimizing domain shift while maximizing feature sharpness.",
        "target_condition": "Pre-detection pipeline prior to YOLOv8 inference.",
        "parameters": {
            "clip_limit": 2.0,
            "tile_grid_size": (8, 8)
        }
    }
}


def get_profile_info(profile_name: str) -> Dict[str, Any]:
    """Retrieves metadata and default parameters for a profile."""
    try:
        p_enum = ProfileName(profile_name)
    except ValueError:
        raise ValueError(f"Unknown profile '{profile_name}'. Valid options: {[p.value for p in ProfileName]}")
    return PROFILE_REGISTRY[p_enum]


def apply_profile(
    profile_name: str,
    image: np.ndarray,
    override_params: Dict[str, Any] = None
) -> EnhancementResult:
    """
    Executes the specified profile on a float32 [0, 1] sonar image.
    """
    info = get_profile_info(profile_name)
    method_name = info["primary_method"].value
    params = dict(info["parameters"])
    if override_params:
        params.update(override_params)

    result = apply_enhancement_method(method_name, image, **params)
    result.profile_used = ProfileName(profile_name)
    return result


def list_profiles() -> List[Dict[str, Any]]:
    """Returns all registered profiles with descriptions and hypotheses."""
    return [
        {
            "id": p.value,
            "name": info["name"],
            "primary_method": info["primary_method"].value,
            "hypothesis": info["hypothesis"],
            "target_condition": info["target_condition"],
            "default_parameters": info["parameters"]
        }
        for p, info in PROFILE_REGISTRY.items()
    ]
