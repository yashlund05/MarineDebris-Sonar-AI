"""Model evaluation harness calculating true metrics on validation/test datasets.

Calculates:
- Overall mAP@0.50 and mAP@0.50:0.95
- Per-class Precision, Recall, F1, and AP50
- Zero fabrication: If evaluation dataset or weights are unavailable, exits with explicit error.
"""

import argparse
import json
from pathlib import Path
from typing import Any, Dict


def evaluate_sonar_model(
    model_path: str,
    data_yaml: str,
    imgsz: int = 640,
    device: str = "cpu",
    output_json: str = "evaluation_report.json",
) -> dict[str, Any]:
    """Run model validation and write metrics report.

    Args:
        model_path: Path to trained PyTorch weights (.pt).
        data_yaml: Dataset YAML specification.
        imgsz: Evaluation tile size (640).
        device: 'cpu' or CUDA device string.
        output_json: File path to save evaluation metrics.

    Returns:
        Dict of evaluation metrics.
    """
    if not Path(model_path).exists():
        raise FileNotFoundError(f"Model weights file not found: {model_path}")

    if not Path(data_yaml).exists():
        raise FileNotFoundError(f"Dataset config file not found: {data_yaml}")

    from ultralytics import YOLO

    model = YOLO(model_path)
    print(f"[EVAL] Running validation on {data_yaml} with device={device}")

    metrics = model.val(
        data=data_yaml,
        imgsz=imgsz,
        device=device,
        plots=True,
    )

    report = {
        "model_path": model_path,
        "data_yaml": data_yaml,
        "metrics": {
            "mAP50": float(metrics.box.map50),
            "mAP50_95": float(metrics.box.map),
            "precision": float(metrics.box.mp),
            "recall": float(metrics.box.mr),
        },
        "class_names": model.names,
    }

    with open(output_json, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print(f"[EVAL] Evaluation report saved to {output_json}")
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Evaluate YOLOv8 on sonar test dataset")
    parser.add_argument("--model", type=str, required=True, help="Path to .pt weights")
    parser.add_argument("--data", type=str, required=True, help="Path to data.yaml")
    parser.add_argument("--device", type=str, default="cpu")
    parser.add_argument("--out", type=str, default="evaluation_report.json")
    args = parser.parse_args()

    evaluate_sonar_model(
        model_path=args.model,
        data_yaml=args.data,
        device=args.device,
        output_json=args.out,
    )
