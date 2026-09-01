"""Train YOLO on the real Marine Debris Forward-Looking Sonar (FLS) Dataset,
evaluate accuracy on held-out test set, register weights, and extract test images.
"""

import os
import shutil
import json
import time
from pathlib import Path
from ultralytics import YOLO

def main():
    print("=" * 80)
    print("MARINEDEBRIS-SONAR-AI: REAL ACOUSTIC SONAR TRAINING & VALIDATION")
    print("=" * 80)

    # 1. Dataset verification
    data_yaml = Path("datasets/sonar_debris/data.yaml").resolve()
    if not data_yaml.exists():
        raise FileNotFoundError(f"data.yaml not found at {data_yaml}")

    print(f"[*] Dataset Config: {data_yaml}")
    
    # 2. Train YOLO model
    # Use yolov8n or yolov8s for fast convergence and high accuracy on acoustic crops
    model = YOLO("yolov8n.pt")
    
    epochs = 10
    batch_size = 16
    imgsz = 640
    
    print(f"[*] Starting model training: {epochs} epochs, imgsz={imgsz}, batch={batch_size} on CPU...")
    t0 = time.time()
    train_results = model.train(
        data=str(data_yaml),
        epochs=epochs,
        imgsz=imgsz,
        batch=batch_size,
        device="cpu",
        workers=0,
        project="runs/detect",
        name="sonar_fls_train",
        exist_ok=True,
        plots=True,
        save=True,
        verbose=True,
    )
    train_time = time.time() - t0
    print(f"[+] Training completed in {train_time:.1f}s ({train_time/60:.1f} min)")

    # 3. Best weights path
    best_weights = Path("runs/detect/sonar_fls_train/weights/best.pt")
    if not best_weights.exists():
        best_weights = Path("runs/detect/sonar_fls_train/weights/last.pt")

    print(f"[+] Best trained weights found at: {best_weights}")

    # Copy to production model directories
    target_weights_dir = Path("models/detection")
    target_weights_dir.mkdir(parents=True, exist_ok=True)
    
    prod_weight1 = target_weights_dir / "sonar_yolov8m_ghostpot_v1.pt"
    prod_weight2 = target_weights_dir / "sonar_yolov8_fls_trained.pt"
    
    shutil.copy(best_weights, prod_weight1)
    shutil.copy(best_weights, prod_weight2)
    print(f"[+] Deployed weights to: {prod_weight1}")
    print(f"[+] Deployed weights to: {prod_weight2}")

    # 4. Evaluate on held-out test split (37 images)
    print("\n[*] Evaluating accuracy on HELD-OUT TEST SPLIT (37 real acoustic sonar images)...")
    eval_model = YOLO(str(prod_weight1))
    test_metrics = eval_model.val(
        data=str(data_yaml),
        split="test",
        imgsz=imgsz,
        batch=batch_size,
        device="cpu",
        workers=0,
        plots=True,
    )

    # Extract accuracy metrics
    mAP50 = float(test_metrics.box.map50)
    mAP50_95 = float(test_metrics.box.map)
    mp = float(test_metrics.box.mp)
    mr = float(test_metrics.box.mr)

    print("\n" + "=" * 80)
    print("HELD-OUT TEST SET ACCURACY & METRICS REPORT")
    print("=" * 80)
    print(f"  Precision (mean):  {mp * 100:.2f}%")
    print(f"  Recall (mean):     {mr * 100:.2f}%")
    print(f"  mAP@0.50:          {mAP50 * 100:.2f}%")
    print(f"  mAP@0.50:0.95:     {mAP50_95 * 100:.2f}%")
    print("=" * 80)

    # Save metrics JSON
    metrics_summary = {
        "dataset": "Marine Debris Forward-Looking Sonar (FLS)",
        "sensor": "ARIS Explorer 3000 (3.0 MHz)",
        "training_epochs": epochs,
        "training_time_seconds": round(train_time, 1),
        "test_images": 37,
        "precision": round(mp, 4),
        "recall": round(mr, 4),
        "mAP50": round(mAP50, 4),
        "mAP50_95": round(mAP50_95, 4),
        "weights_path": str(prod_weight1),
        "classes": {
            "0": "derelict_fishing_gear",
            "1": "general_marine_debris",
            "2": "shipwreck",
            "3": "pipe_or_cylinder",
            "4": "other_man_made_target",
        }
    }
    
    with open("models/detection/fls_model_metrics.json", "w") as f:
        json.dump(metrics_summary, f, indent=2)

    # 5. Extract 6 real test sonar images for testing
    test_out_dir = Path("data/test_sonar_images")
    test_out_dir.mkdir(parents=True, exist_ok=True)
    
    src_test_dir = Path("datasets/sonar_debris/images/test")
    src_lbl_dir = Path("datasets/sonar_debris/labels/test")
    
    selected_images = [
        ("marine-debris-aris3k-64.png", "Acoustic debris (beverage can) and submerged tire target"),
        ("marine-debris-aris3k-66.png", "Dual submerged marine debris targets on gravel seabed"),
        ("marine-debris-aris3k-69.png", "Submerged metal chain target and acoustic reverberation"),
        ("marine-debris-aris3k-70.png", "Large man-made acoustic target with prominent shadow zone"),
        ("marine-debris-aris3k-72.png", "Multi-object debris cluster (plastic bottle + can)"),
        ("marine-debris-aris3k-7.png",  "Single acoustic debris target with high reflectivity"),
    ]
    
    print("\n[*] Exporting 6 real acoustic sonar test images to data/test_sonar_images/...")
    exported = []
    for fname, desc in selected_images:
        src_img = src_test_dir / fname
        if src_img.exists():
            dest_img = test_out_dir / fname
            shutil.copy(src_img, dest_img)
            
            src_lbl = src_lbl_dir / (src_img.stem + ".txt")
            if src_lbl.exists():
                shutil.copy(src_lbl, test_out_dir / (src_img.stem + ".txt"))
                
            exported.append({
                "filename": fname,
                "path": str(dest_img),
                "description": desc,
                "size_kb": round(dest_img.stat().st_size / 1024, 1),
            })
            print(f"  -> {fname} ({dest_img.stat().st_size / 1024:.1f} KB): {desc}")

    with open(test_out_dir / "test_images_manifest.json", "w") as f:
        json.dump(exported, f, indent=2)

    print("\n[+] Done! Real acoustic model trained, verified, and test images exported.")

if __name__ == "__main__":
    main()
