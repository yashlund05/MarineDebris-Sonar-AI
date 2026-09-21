"""Deterministic test fixtures for Live Sonar AI Detection & Tracking Subsystem."""

from pathlib import Path

FIXTURES_DIR = Path(__file__).resolve().parent
SEQUENCE_DIR = FIXTURES_DIR / "sequence"
REPLAY_VIDEO_PATH = FIXTURES_DIR / "aris3k_replay_stream.mp4"
ORACLE_MANIFEST_PATH = FIXTURES_DIR / "ground_truth_oracle.json"
