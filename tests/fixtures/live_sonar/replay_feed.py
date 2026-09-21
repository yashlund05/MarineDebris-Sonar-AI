"""Deterministic Replay Feed Generator for Live Sonar Testing.

Builds and serves deterministic replay test fixtures derived from verified
ARIS 3000 (3.0 MHz) Forward-Looking Sonar (FLS) imagery in `data/test_sonar_images/`.
"""

import os
import json
import shutil
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
from datetime import datetime, timezone
import numpy as np
import cv2
from PIL import Image

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
TEST_IMAGES_DIR = REPO_ROOT / "data" / "test_sonar_images"
MANIFEST_PATH = TEST_IMAGES_DIR / "manifest.json"
FIXTURES_DIR = Path(__file__).resolve().parent
SEQUENCE_DIR = FIXTURES_DIR / "sequence"
REPLAY_VIDEO_PATH = FIXTURES_DIR / "aris3k_replay_stream.mp4"
ORACLE_MANIFEST_PATH = FIXTURES_DIR / "ground_truth_oracle.json"


def get_ground_truth_manifest() -> List[Dict[str, Any]]:
    """Load the ground truth manifest for test sonar images."""
    if not MANIFEST_PATH.exists():
        raise FileNotFoundError(f"Source manifest not found at {MANIFEST_PATH}")
    with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def get_sample_fls_image_paths() -> List[Path]:
    """Return sorted list of verified ARIS 3000 FLS test image paths."""
    manifest = get_ground_truth_manifest()
    paths = []
    for item in manifest:
        p = REPO_ROOT / item["relative_path"]
        if p.exists():
            paths.append(p)
    return paths


def get_sample_fls_image_arrays() -> List[np.ndarray]:
    """Load verified ARIS 3000 FLS images as numpy arrays (grayscale uint8)."""
    paths = get_sample_fls_image_paths()
    arrays = []
    for p in paths:
        img = cv2.imread(str(p), cv2.IMREAD_GRAYSCALE)
        if img is not None:
            arrays.append(img)
    return arrays


def build_frame_sequence() -> Path:
    """Create directory of sequenced PNG frames with JSON telemetry sidecars."""
    SEQUENCE_DIR.mkdir(parents=True, exist_ok=True)
    manifest = get_ground_truth_manifest()
    
    # Authentic ARIS 3000 operating telemetry
    base_telemetry = {
        "frequency_hz": 3000000.0,  # 3.0 MHz
        "range_m": 15.0,            # 15 meter acoustic sweep
        "gain_db": 42.5,
        "beam_angle_deg": 28.0,
        "sound_speed_mps": 1500.0,
        "heading_deg": 184.2,
        "pitch_deg": -1.5,
        "roll_deg": 0.8,
        "depth_m": 12.4
    }

    base_nav = {
        "latitude": 38.812345,
        "longitude": -75.134567,
        "heading_deg": 184.2,
        "depth_m": 12.4,
        "speed_knots": 2.1
    }

    for idx, item in enumerate(manifest):
        src_path = REPO_ROOT / item["relative_path"]
        dst_img_path = SEQUENCE_DIR / f"frame_{idx:04d}.png"
        dst_meta_path = SEQUENCE_DIR / f"frame_{idx:04d}_meta.json"

        # Copy authentic image
        if src_path.exists():
            shutil.copyfile(src_path, dst_img_path)

        # Parse ground truth boxes
        raw_gt = item.get("ground_truth", "")
        parsed_gt = []
        for line in raw_gt.strip().split("\n"):
            parts = line.strip().split()
            if len(parts) >= 5:
                parsed_gt.append({
                    "class_id": int(parts[0]),
                    "x_center": float(parts[1]),
                    "y_center": float(parts[2]),
                    "width": float(parts[3]),
                    "height": float(parts[4])
                })

        meta = {
            "sequence_number": idx,
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "source_image": item["filename"],
            "description": item["description"],
            "sonar_metadata": base_telemetry,
            "navigation": base_nav,
            "ground_truth": parsed_gt
        }

        with open(dst_meta_path, "w", encoding="utf-8") as f:
            json.dump(meta, f, indent=2)

    return SEQUENCE_DIR


def build_replay_video(fps: float = 15.0, duration_repeats: int = 5) -> Path:
    """Compile authentic ARIS 3000 images into a deterministic MP4 video."""
    images = get_sample_fls_image_arrays()
    if not images:
        raise RuntimeError("No ARIS 3000 images available to build replay video.")

    h, w = images[0].shape
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out = cv2.VideoWriter(str(REPLAY_VIDEO_PATH), fourcc, fps, (w, h), isColor=False)

    try:
        for _ in range(duration_repeats):
            for img in images:
                out.write(img)
    finally:
        out.release()

    return REPLAY_VIDEO_PATH


def export_ground_truth_oracle() -> Path:
    """Generate the authoritative detection expectation oracle file."""
    manifest = get_ground_truth_manifest()
    oracle = {
        "model_checkpoint": "models/detection/sonar_yolov8_fls_trained.pt",
        "model_expected_sha256": "e1215c7e7f6e4f3722398bf93d975eb5013c49f78355d0d5f54ce982d495b3d7",
        "classes": {
            "0": "derelict_fishing_gear",
            "1": "general_marine_debris",
            "2": "shipwreck",
            "3": "pipe_or_cylinder",
            "4": "other_man_made_target"
        },
        "frames": manifest
    }
    with open(ORACLE_MANIFEST_PATH, "w", encoding="utf-8") as f:
        json.dump(oracle, f, indent=2)
    return ORACLE_MANIFEST_PATH


def ensure_fixtures_built():
    """Ensure all physical replay fixtures exist on disk."""
    if not SEQUENCE_DIR.exists() or len(list(SEQUENCE_DIR.glob("*.png"))) == 0:
        build_frame_sequence()
    if not REPLAY_VIDEO_PATH.exists() or REPLAY_VIDEO_PATH.stat().st_size == 0:
        build_replay_video()
    if not ORACLE_MANIFEST_PATH.exists():
        export_ground_truth_oracle()


if __name__ == "__main__":
    print("Building deterministic replay fixtures...")
    build_frame_sequence()
    build_replay_video()
    export_ground_truth_oracle()
    print(f"Sequence created at: {SEQUENCE_DIR}")
    print(f"Replay video created at: {REPLAY_VIDEO_PATH}")
    print(f"Oracle manifest created at: {ORACLE_MANIFEST_PATH}")
