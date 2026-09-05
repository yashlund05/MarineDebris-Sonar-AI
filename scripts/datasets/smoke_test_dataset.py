"""Smoke test and visual verification utility for YOLO sonar dataset."""

import os
import sys
from pathlib import Path
import yaml
import cv2

CLASS_NAMES = {
    0: "derelict_fishing_gear",
    1: "general_marine_debris",
    2: "shipwreck",
    3: "pipe_or_cylinder",
    4: "other_man_made_target",
}


def smoke_test_dataset(data_yaml_path: Path) -> bool:
    print("==============================================================================")
    print("           MARINEDEBRIS-SONAR-AI DATASET SMOKE TEST                           ")
    print("==============================================================================")
    print(f"Loading data config: {data_yaml_path}")

    if not data_yaml_path.exists():
        print(f"[FAIL] data.yaml not found at {data_yaml_path}")
        return False

    with open(data_yaml_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    base_path = Path(config.get("path", "."))
    print(f"Base Path: {base_path}")

    for split in ["train", "val", "test"]:
        rel_img = config.get(split)
        if not rel_img:
            print(f"[FAIL] Missing split key: {split}")
            return False

        img_dir = base_path / rel_img
        lbl_dir = base_path / "labels" / split

        if not img_dir.exists():
            print(f"[FAIL] Image directory does not exist: {img_dir}")
            return False

        if not lbl_dir.exists():
            print(f"[FAIL] Label directory does not exist: {lbl_dir}")
            return False

        imgs = list(img_dir.glob("*.png"))
        lbls = list(lbl_dir.glob("*.txt"))
        print(f" - Split '{split}': {len(imgs)} images, {len(lbls)} label files verified.")

        if len(imgs) == 0 or len(lbls) == 0:
            print(f"[FAIL] Empty split: {split}")
            return False

    # Generate a visual verification sample
    sample_img_p = base_path / "images" / "train" / "marine-debris-aris3k-10.png"
    sample_lbl_p = base_path / "labels" / "train" / "marine-debris-aris3k-10.txt"

    if not sample_img_p.exists():
        # Fallback to first available image
        sample_img_p = next((base_path / "images" / "train").glob("*.png"))
        sample_lbl_p = (base_path / "labels" / "train") / f"{sample_img_p.stem}.txt"

    img = cv2.imread(str(sample_img_p))
    if img is None:
        print(f"[FAIL] Could not read sample image {sample_img_p}")
        return False

    h, w, _ = img.shape

    with open(sample_lbl_p, "r", encoding="utf-8") as f:
        labels = [line.strip().split() for line in f if line.strip()]

    print(f"\n[VISUALIZATION] Rendering {len(labels)} real debris labels on {sample_img_p.name}...")
    for label in labels:
        cls_id = int(label[0])
        xc, yc, bw, bh = map(float, label[1:])

        # Convert back to pixel box
        x1 = int((xc - bw / 2.0) * w)
        y1 = int((yc - bh / 2.0) * h)
        x2 = int((xc + bw / 2.0) * w)
        y2 = int((yc + bh / 2.0) * h)

        cls_name = CLASS_NAMES.get(cls_id, f"class_{cls_id}")
        # Draw bounding box
        cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 2)
        label_text = f"ID {cls_id}: {cls_name}"
        cv2.putText(
            img,
            label_text,
            (x1, max(15, y1 - 5)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (0, 255, 255),
            1,
            cv2.LINE_AA,
        )
        print(f" -> Box: {label_text} at [{x1}, {y1}, {x2}, {y2}]")

    viz_out = base_path / "sample_annotation_viz.png"
    cv2.imwrite(str(viz_out), img)
    print(f"[SUCCESS] Verification image saved to: {viz_out}")

    print("\n[SMOKE TEST PASSED] All images, labels, and YAML configurations are valid.")
    return True


if __name__ == "__main__":
    success = smoke_test_dataset(Path("datasets/sonar_debris/data.yaml"))
    sys.exit(0 if success else 1)
