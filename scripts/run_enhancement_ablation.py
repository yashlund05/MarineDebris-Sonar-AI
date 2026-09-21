"""
MarineDebris-Sonar-AI: Stage-by-Stage Enhancement Ablation & Parameter Sweep
Quantifies the exact downstream YOLO impact of individual enhancement components:
- CLAHE (clip 1.2, 1.8, 3.0)
- Speckle Filtering (Lee Filter k=3, k=5)
- Periodic Stripe Notch Filtering
- Gamma Mapping (0.85, 1.15)
"""

import sys
import json
import time
from pathlib import Path
import numpy as np
import cv2
from ultralytics import YOLO

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from backend.enhancement.stages.stripe_filter import StripeNoiseNotchStage
from backend.enhancement.stages.speckle_filter import SpeckleDenoisingStage
from backend.enhancement.stages.contrast_stage import AdaptiveContrastStage
from backend.enhancement.pipeline_base import SonarEnhancementContext, Modality, SignalRepresentation, ProcessingMode


def compute_iou(b1, b2):
    cx1, cy1, w1, h1 = b1
    cx2, cy2, w2, h2 = b2
    xA = max(cx1 - w1/2, cx2 - w2/2)
    yA = max(cy1 - h1/2, cy2 - h2/2)
    xB = min(cx1 + w1/2, cx2 + w2/2)
    yB = min(cy1 + h1/2, cy2 + h2/2)
    inter = max(0.0, xB - xA) * max(0.0, yB - yA)
    union = (w1 * h1) + (w2 * h2) - inter
    return inter / union if union > 0 else 0.0


def evaluate_stage_on_yolo(model, stage_name, transform_fn, images, labels_dir):
    total_gt = 0
    total_pred = 0
    tp = 0
    fp = 0
    fn = 0
    times = []

    for p in images[:25]:
        txt_path = labels_dir / f"{p.stem}.txt"
        gt_boxes = []
        if txt_path.exists():
            with open(txt_path, "r") as f:
                for line in f:
                    parts = line.strip().split()
                    if len(parts) == 5:
                        gt_boxes.append([int(parts[0])] + [float(x) for x in parts[1:]])
        total_gt += len(gt_boxes)

        img_bgr = cv2.imread(str(p))
        if img_bgr is None:
            continue
        gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
        norm_gray = gray.astype(np.float32) / 255.0

        t0 = time.perf_counter()
        transformed = transform_fn(norm_gray, p.stem)
        enh_uint8 = np.clip(transformed * 255.0, 0, 255).astype(np.uint8)
        enh_3ch = cv2.cvtColor(enh_uint8, cv2.COLOR_GRAY2BGR)

        preds = model.predict(enh_3ch, conf=0.25, iou=0.45, verbose=False)[0]
        times.append((time.perf_counter() - t0) * 1000.0)

        pred_boxes = []
        if preds.boxes is not None:
            for b in preds.boxes:
                cid = int(b.cls.item())
                xywhn = b.xywhn[0].cpu().numpy().tolist()
                pred_boxes.append([cid] + xywhn)
        total_pred += len(pred_boxes)

        matched = set()
        for pb in pred_boxes:
            best_iou = 0.0
            best_idx = -1
            for g_idx, gb in enumerate(gt_boxes):
                if g_idx in matched:
                    continue
                if pb[0] == gb[0]:
                    iou = compute_iou(pb[1:], gb[1:])
                    if iou > best_iou:
                        best_iou = iou
                        best_idx = g_idx
            if best_iou >= 0.45:
                tp += 1
                matched.add(best_idx)
            else:
                fp += 1

        fn += (len(gt_boxes) - len(matched))

    prec = tp / total_pred if total_pred > 0 else 0.0
    rec = tp / total_gt if total_gt > 0 else 0.0
    f1 = (2 * prec * rec) / (prec + rec) if (prec + rec) > 0 else 0.0

    return {
        "stage": stage_name,
        "precision": round(prec, 4),
        "recall": round(rec, 4),
        "f1": round(f1, 4),
        "latency_ms": round(float(np.mean(times)), 2),
    }


def main():
    prod_path = ROOT_DIR / "models" / "detection" / "sonar_yolov8_fls_trained.pt"
    model = YOLO(str(prod_path))

    images = sorted(list((ROOT_DIR / "datasets" / "sonar_debris_v3" / "images" / "test").glob("*.png")))
    labels = ROOT_DIR / "datasets" / "sonar_debris_v3" / "labels" / "test"

    print("Running Stage-by-Stage Downstream YOLO Ablation...")

    # Define stage transform functions
    def raw_tf(img, stem): return img
    def clahe_12_tf(img, stem):
        st = AdaptiveContrastStage(clip_limit=1.2, tile_grid_size=(8, 8))
        ctx = SonarEnhancementContext(artifact_id=stem, modality=Modality.FLS)
        return st.process(img, ctx)[0]

    def clahe_18_tf(img, stem):
        st = AdaptiveContrastStage(clip_limit=1.8, tile_grid_size=(8, 8))
        ctx = SonarEnhancementContext(artifact_id=stem, modality=Modality.FLS)
        return st.process(img, ctx)[0]

    def clahe_30_tf(img, stem):
        st = AdaptiveContrastStage(clip_limit=3.0, tile_grid_size=(8, 8))
        ctx = SonarEnhancementContext(artifact_id=stem, modality=Modality.FLS)
        return st.process(img, ctx)[0]

    def lee_k3_tf(img, stem):
        st = SpeckleDenoisingStage(method="lee", window_size=3)
        ctx = SonarEnhancementContext(artifact_id=stem, modality=Modality.FLS)
        return st.process(img, ctx)[0]

    def lee_k5_tf(img, stem):
        st = SpeckleDenoisingStage(method="lee", window_size=5)
        ctx = SonarEnhancementContext(artifact_id=stem, modality=Modality.FLS)
        return st.process(img, ctx)[0]

    def stripe_tf(img, stem):
        st = StripeNoiseNotchStage()
        ctx = SonarEnhancementContext(artifact_id=stem, modality=Modality.FLS)
        return st.process(img, ctx)[0]

    def gamma_085_tf(img, stem):
        return np.power(img, 0.85)

    def gamma_115_tf(img, stem):
        return np.power(img, 1.15)

    ablations = [
        ("RAW_BASELINE", raw_tf),
        ("RAW_PLUS_CLAHE_1.2", clahe_12_tf),
        ("RAW_PLUS_CLAHE_1.8", clahe_18_tf),
        ("RAW_PLUS_CLAHE_3.0", clahe_30_tf),
        ("RAW_PLUS_LEE_K3", lee_k3_tf),
        ("RAW_PLUS_LEE_K5", lee_k5_tf),
        ("RAW_PLUS_STRIPE_NOTCH", stripe_tf),
        ("RAW_PLUS_GAMMA_0.85", gamma_085_tf),
        ("RAW_PLUS_GAMMA_1.15", gamma_115_tf),
    ]

    results = {}
    for name, tf in ablations:
        res = evaluate_stage_on_yolo(model, name, tf, images, labels)
        results[name] = res
        print(f"  {name:24s} -> Prec: {res['precision']:.4f}, Rec: {res['recall']:.4f}, F1: {res['f1']:.4f}, Latency: {res['latency_ms']:.1f}ms")

    out_file = ROOT_DIR / "reports" / "enhancement_ablation.json"
    with open(out_file, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\n[+] Saved ablation report to: {out_file}")


if __name__ == "__main__":
    main()
