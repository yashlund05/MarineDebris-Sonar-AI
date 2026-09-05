"""
MarineDebris-Sonar-AI: Optimization Utilities
Provides cryptographic hashing, environment tracking, production lock verification,
and diagnostic helpers.
"""

import os
import sys
import hashlib
import platform
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional
import torch

ROOT_DIR = Path(__file__).resolve().parents[3]
PRODUCTION_CHECKPOINT_PATH = ROOT_DIR / "models" / "detection" / "sonar_yolov8_fls_trained.pt"
FROZEN_PRODUCTION_SHA256 = "e1215c7e7f6e4f3722398bf93d975eb5013c49f78355d0d5f54ce982d495b3d7"


def compute_sha256(file_path: Path) -> str:
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def verify_production_checkpoint() -> bool:
    """
    Guarantees production model checkpoint is immutable and has not been altered.
    Raises RuntimeError immediately if file is missing or hash does not match.
    """
    if not PRODUCTION_CHECKPOINT_PATH.exists():
        raise RuntimeError(
            f"PRODUCTION BASELINE INTEGRITY FAILURE: Production checkpoint missing at {PRODUCTION_CHECKPOINT_PATH}"
        )
    current_sha = compute_sha256(PRODUCTION_CHECKPOINT_PATH)
    if current_sha != FROZEN_PRODUCTION_SHA256:
        raise RuntimeError(
            f"PRODUCTION BASELINE INTEGRITY FAILURE:\n"
            f"Expected: {FROZEN_PRODUCTION_SHA256}\n"
            f"Found:    {current_sha}"
        )
    return True


def get_git_commit() -> Optional[str]:
    try:
        res = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=str(ROOT_DIR),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
        )
        if res.returncode == 0:
            return res.stdout.strip()
    except Exception:
        pass
    return None


def get_system_environment() -> Dict[str, Any]:
    import ultralytics
    import cv2
    import numpy as np

    env = {
        "os": f"{platform.system()} {platform.release()}",
        "python": platform.python_version(),
        "torch": torch.__version__,
        "ultralytics": ultralytics.__version__,
        "opencv": cv2.__version__,
        "numpy": np.__version__,
        "cuda_available": torch.cuda.is_available(),
        "device": "cuda" if torch.cuda.is_available() else "cpu",
        "cpu_count": os.cpu_count(),
        "torch_threads": torch.get_num_threads(),
        "git_commit": get_git_commit(),
    }
    if torch.cuda.is_available():
        env["cuda_device_name"] = torch.cuda.get_device_name(0)
    return env
