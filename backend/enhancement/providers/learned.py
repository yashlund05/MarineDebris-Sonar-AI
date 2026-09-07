"""
Learned Enhancement Provider supporting deep learning sonar despeckling models (SEGSID / WFC-BSN).

Scientific Integrity Rule:
If model weights are missing or not validated, the provider truthfully reports
status='UNAVAILABLE' or 'EXPERIMENTAL'. It NEVER fabricates outputs.
"""

from pathlib import Path
from typing import Dict, Any, Optional
import numpy as np
import logging
from backend.enhancement.providers.base import EnhancementProvider
from backend.enhancement.types import EnhancementResult, EnhancementMethod

logger = logging.getLogger(__name__)

MODELS_DIR = Path(__file__).resolve().parent.parent.parent.parent / "models" / "enhancement"


class LearnedEnhancementProvider(EnhancementProvider):
    """
    Adapter for learned sonar despeckling architectures (SEGSID-KD / WFC-BSN).
    Enforces non-generative, dimension-preserving, single-channel float32 execution.
    """

    def __init__(
        self,
        model_name: str = "segsid_kd_debris",
        weights_filename: str = "segsid_kd_debris.pt",
        device: str = "cpu"
    ):
        self._name = model_name
        self._version = "0.9.0-candidate"
        self._weights_path = MODELS_DIR / weights_filename
        self._device = device
        self._model = None
        self._loaded = False
        self._init_model()

    def _init_model(self):
        """Attempts to load checkpoint safely if resident."""
        if not self._weights_path.exists():
            self._status = "UNAVAILABLE"
            logger.info("Learned weights not present at %s. Marked as UNAVAILABLE.", self._weights_path)
            return

        try:
            import torch
            # Safe checkpoint loading
            self._model = torch.load(str(self._weights_path), map_location=self._device)
            if hasattr(self._model, "eval"):
                self._model.eval()
            self._loaded = True
            self._status = "EXPERIMENTAL"
            logger.info("Loaded learned model %s on device %s", self._name, self._device)
        except Exception as e:
            logger.warning("Could not load weights for %s: %s", self._name, str(e))
            self._status = "ERROR"

    @property
    def name(self) -> str:
        return self._name

    @property
    def version(self) -> str:
        return self._version

    @property
    def provider_type(self) -> str:
        return "learned"

    @property
    def validation_status(self) -> str:
        return self._status

    def supports(self, image: np.ndarray) -> bool:
        if not self._loaded or image.size == 0:
            return False
        return True

    def enhance(
        self,
        image: np.ndarray,
        parameters: Optional[Dict[str, Any]] = None
    ) -> EnhancementResult:
        if not self._loaded or self._model is None:
            raise RuntimeError(
                f"Learned model '{self.name}' is UNAVAILABLE. "
                "Requires task-specific weights. Fall back to classical provider."
            )

        import time
        import torch

        t0 = time.perf_counter()
        img = image.astype(np.float32)
        if img.ndim == 3 and img.shape[2] == 1:
            img = img.squeeze(axis=2)

        H, W = img.shape
        tensor = torch.from_numpy(img).unsqueeze(0).unsqueeze(0).to(self._device)

        with torch.inference_mode():
            out_tensor = self._model(tensor)
            if isinstance(out_tensor, tuple):
                out_tensor = out_tensor[0]
            out_np = out_tensor.squeeze().cpu().numpy().astype(np.float32)

        # Enforce canonical invariants
        out_np = np.clip(out_np, 0.0, 1.0)
        if out_np.shape != (H, W):
            import cv2
            out_np = cv2.resize(out_np, (W, H), interpolation=cv2.INTER_LINEAR)

        dt_ms = (time.perf_counter() - t0) * 1000.0

        return EnhancementResult(
            canonical_image=out_np,
            method=EnhancementMethod.IDENTITY,
            parameters={"model": self.name, "device": self._device},
            execution_time_ms=round(dt_ms, 3)
        )

    def metadata(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "version": self.version,
            "type": self.provider_type,
            "status": self.validation_status,
            "weights_path": str(self._weights_path),
            "weights_present": self._weights_path.exists(),
            "device": self._device,
            "architecture": "Self-Supervised Blind-Spot Network + Distillation",
            "citation": "Liu et al., IEEE TIP 2025",
        }

    def health_check(self) -> Dict[str, Any]:
        return {
            "provider": self.name,
            "type": self.provider_type,
            "status": self.validation_status,
            "ready": self._loaded,
            "weights_found": self._weights_path.exists(),
            "device": self._device,
        }
