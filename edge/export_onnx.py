"""Export YOLOv8 PyTorch detection model to ONNX for edge deployment.

Target edge hardware: NVIDIA Jetson Orin Nano / AGX Orin / Raspberry Pi 5.
"""

import argparse
from pathlib import Path


def export_to_onnx(
    model_path: str,
    imgsz: int = 640,
    opset: int = 17,
    dynamic: bool = True,
    simplify: bool = True,
) -> str:
    """Export trained YOLOv8 weights to ONNX format.

    Args:
        model_path: Path to PyTorch .pt weights file.
        imgsz: Input resolution (640).
        opset: ONNX operator set version (17).
        dynamic: Support dynamic batch sizes.
        simplify: Run onnxsim graph optimization.

    Returns:
        Path to exported .onnx model.
    """
    if not Path(model_path).exists():
        raise FileNotFoundError(f"Model file not found: {model_path}")

    from ultralytics import YOLO

    print(f"[EDGE] Loading model from {model_path}")
    model = YOLO(model_path)

    print(f"[EDGE] Exporting to ONNX (imgsz={imgsz}, opset={opset}, dynamic={dynamic})")
    onnx_file = model.export(
        format="onnx",
        imgsz=imgsz,
        opset=opset,
        dynamic=dynamic,
        simplify=simplify,
    )

    print(f"[EDGE] Successfully exported ONNX model to: {onnx_file}")
    return str(onnx_file)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Export YOLOv8 to ONNX format for edge deployment")
    parser.add_argument("--model", type=str, required=True, help="Path to .pt weights")
    parser.add_argument("--imgsz", type=int, default=640)
    parser.add_argument("--opset", type=int, default=17)
    args = parser.parse_args()

    export_to_onnx(model_path=args.model, imgsz=args.imgsz, opset=args.opset)
