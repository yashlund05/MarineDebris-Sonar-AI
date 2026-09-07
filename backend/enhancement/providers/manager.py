"""
Enhancement Provider Manager and Unified Pipeline Orchestrator.

Implements AUTO / RECOMMENDED resolution, provider health dispatching,
and deterministic SHA-256 caching for the project-wide enhancement system.
"""

import hashlib
import json
import logging
from typing import Dict, Any, Optional, Tuple
import numpy as np

from backend.enhancement.types import EnhancementResult, ProfileName, EnhancementMethod
from backend.enhancement.providers.base import EnhancementProvider
from backend.enhancement.providers.classical import ClassicalEnhancementProvider
from backend.enhancement.providers.learned import LearnedEnhancementProvider
from backend.enhancement.profiles import apply_profile, PROFILE_REGISTRY

logger = logging.getLogger(__name__)


class EnhancementManager:
    """Central orchestrator managing enhancement providers and cache lookup."""

    _instance: Optional["EnhancementManager"] = None

    def __init__(self):
        self.classical_provider = ClassicalEnhancementProvider()
        self.learned_provider = LearnedEnhancementProvider()
        # In-memory bounded cache for processed frames
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._cache_capacity = 256

    @classmethod
    def get_instance(cls) -> "EnhancementManager":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def compute_cache_key(
        self,
        image_bytes_or_array: np.ndarray,
        method: str,
        profile: Optional[str],
        parameters: Dict[str, Any],
        palette: str
    ) -> str:
        """Computes deterministic SHA256 cache key."""
        h = hashlib.sha256()
        # Hash image data
        if isinstance(image_bytes_or_array, np.ndarray):
            h.update(image_bytes_or_array.tobytes())
        elif isinstance(image_bytes_or_array, bytes):
            h.update(image_bytes_or_array)
        else:
            h.update(str(image_bytes_or_array).encode("utf-8"))

        h.update(method.encode("utf-8"))
        h.update((profile or "none").encode("utf-8"))
        h.update(json.dumps(parameters, sort_keys=True).encode("utf-8"))
        h.update(palette.encode("utf-8"))
        h.update(b"v1.0.0")  # Engine version
        return h.hexdigest()

    def improve_sonar_image(
        self,
        image: np.ndarray,
        method: str = "auto",
        profile: Optional[str] = None,
        parameters: Optional[Dict[str, Any]] = None,
        palette: str = "amber",
        allow_cache: bool = True
    ) -> Tuple[EnhancementResult, Dict[str, Any]]:
        """
        Primary entry point for project-wide sonar image improvement.
        
        Resolution Order for 'auto':
        1. Learned Model (if resident and validated)
        2. Classical Validated Default (Bilateral + CLAHE / BALANCED profile)
        
        Returns:
            (enhancement_result, execution_telemetry)
        """
        params = dict(parameters or {})
        cache_key = self.compute_cache_key(image, method, profile, params, palette)

        # Check Cache
        if allow_cache and cache_key in self._cache:
            entry = self._cache[cache_key]
            logger.debug("Cache hit for enhancement key %s", cache_key[:12])
            telemetry = dict(entry["telemetry"])
            telemetry["cache_hit"] = True
            return entry["result"], telemetry

        provider_used = "classical"
        engine_status = "VALIDATED"
        fallback_applied = False

        # 1. AUTO / RECOMMENDED resolution
        if method.lower() == "auto":
            if self.learned_provider.supports(image):
                try:
                    res = self.learned_provider.enhance(image, params)
                    provider_used = "learned"
                    engine_status = self.learned_provider.validation_status
                except Exception as e:
                    logger.warning("Learned enhancement failed (%s). Triggering classical fallback.", e)
                    fallback_applied = True
                    res = apply_profile(ProfileName.BALANCED.value, image, override_params=params)
                    provider_used = "classical_fallback"
                    engine_status = "CLASSICAL_FALLBACK"
            else:
                # Default to validated BALANCED classical profile
                res = apply_profile(ProfileName.BALANCED.value, image, override_params=params)
                provider_used = "classical"
                engine_status = "VALIDATED"

        elif method.lower() == "learned":
            if self.learned_provider.supports(image):
                try:
                    res = self.learned_provider.enhance(image, params)
                    provider_used = "learned"
                    engine_status = self.learned_provider.validation_status
                except Exception as e:
                    logger.warning("Learned provider failed. Falling back to classical.")
                    fallback_applied = True
                    res = apply_profile(ProfileName.BALANCED.value, image, override_params=params)
                    provider_used = "classical_fallback"
                    engine_status = "CLASSICAL_FALLBACK"
            else:
                fallback_applied = True
                res = apply_profile(ProfileName.BALANCED.value, image, override_params=params)
                provider_used = "classical_fallback"
                engine_status = "CLASSICAL_FALLBACK"

        elif profile:
            res = apply_profile(profile, image, override_params=params)
            provider_used = "classical"
            engine_status = "VALIDATED"

        else:
            # Specific classical method requested
            res = self.classical_provider.enhance(image, {"method": method, **params})
            provider_used = "classical"
            engine_status = "VALIDATED"

        telemetry = {
            "cache_hit": False,
            "cache_key": cache_key,
            "provider_used": provider_used,
            "engine_status": engine_status,
            "fallback_applied": fallback_applied,
            "execution_time_ms": res.execution_time_ms,
            "engine_version": "1.0.0",
        }

        # Store in bounded cache
        if len(self._cache) >= self._cache_capacity:
            # Evict oldest item
            first_key = next(iter(self._cache))
            del self._cache[first_key]

        self._cache[cache_key] = {"result": res, "telemetry": telemetry}
        return res, telemetry

    def get_providers_status(self) -> Dict[str, Any]:
        """Returns health status of all registered enhancement backends."""
        return {
            "classical": self.classical_provider.health_check(),
            "learned": self.learned_provider.health_check(),
            "cache_entries": len(self._cache),
            "cache_capacity": self._cache_capacity,
        }
