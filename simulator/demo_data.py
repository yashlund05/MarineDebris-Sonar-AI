"""Seed demonstration synthetic surveys for integration testing and local development.

Creates realistic synthetic acoustic records tagged with:
  source_type="SYNTHETIC"
  mode="DEMO"
"""

import os
from pathlib import Path
from simulator.generator import SonarSimulator


def seed_demo_surveys(output_dir: str = "data/demo") -> list[str]:
    """Generate 2 synthetic demo surveys with ground truth labels.

    Args:
        output_dir: Destination folder.

    Returns:
        List of generated sample filepaths.
    """
    sim = SonarSimulator(width=1024, height=1200)
    samples = []

    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    print(f"[SIMULATOR] Generating synthetic demo sonar strip 1...")
    m1 = sim.export_synthetic_sample(output_dir, sample_name="demo_synthetic_survey_starboard", num_targets=5)
    samples.append(str(out / "demo_synthetic_survey_starboard.png"))

    print(f"[SIMULATOR] Generating synthetic demo sonar strip 2...")
    m2 = sim.export_synthetic_sample(output_dir, sample_name="demo_synthetic_survey_port", num_targets=4)
    samples.append(str(out / "demo_synthetic_survey_port.png"))

    print(f"[SIMULATOR] Generated {len(samples)} demonstration surveys in {output_dir}")
    return samples


if __name__ == "__main__":
    seed_demo_surveys()
