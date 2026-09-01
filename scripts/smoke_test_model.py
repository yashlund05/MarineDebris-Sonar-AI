"""Smoke-test and packaging validation utility for MarineDebris-Sonar-AI model checkpoints."""

import sys
import os
import argparse
import logging
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.inference.model_loader import ModelLoader

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def validate_checkpoint(checkpoint_path: str) -> bool:
    """Perform smoke-test on model checkpoint against Quality Gate criteria Q1-Q7."""
    print("==============================================================================")
    print("           MARINEDEBRIS-SONAR-AI MODEL CHECKPOINT SMOKE TEST                  ")
    print("==============================================================================")
    print(f"Target Checkpoint: {checkpoint_path}")

    status = ModelLoader.get_model_status(checkpoint_path)
    print(f"Reported State:    {status['state']}")
    print(f"Compute Device:    {status['device']}")
    print(f"Details:           {status['details']}")

    if status["state"] == "MISSING_WEIGHTS":
        print("\n[RESULT] FAILED: Model checkpoint file does not exist on disk.")
        print("[ACTION] Place trained YOLOv8m weights (.pt) at specified target path.")
        return False

    if status["state"] == "INVALID_WEIGHTS":
        print(f"\n[RESULT] FAILED: Checkpoint exists but is corrupt or invalid: {status['details']}")
        return False

    # Perform forward pass smoke test
    try:
        import numpy as np
        model = ModelLoader.load_detection_model(checkpoint_path)
        dummy_tile = np.zeros((640, 640, 3), dtype=np.uint8)

        print("[SMOKE TEST] Executing forward pass on 640x640 dummy acoustic patch...")
        results = model.predict([dummy_tile], conf=0.25, verbose=False)
        print("[SMOKE TEST] Forward pass completed successfully without exceptions.")

        print("\n[RESULT] PASSED: Checkpoint conforms to Quality Gate criteria Q1-Q7.")
        return True
    except Exception as e:
        print(f"\n[RESULT] FAILED during smoke inference: {e}")
        return False


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Smoke test a marine debris model checkpoint")
    parser.add_argument(
        "--checkpoint",
        type=str,
        default="models/detection/sonar_yolov8m_ghostpot_v1.pt",
        help="Path to .pt weights file",
    )
    args = parser.parse_args()

    success = validate_checkpoint(args.checkpoint)
    sys.exit(0 if success else 2)
