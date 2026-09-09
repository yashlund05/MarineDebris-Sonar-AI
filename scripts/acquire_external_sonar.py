"""Reproducible Acquisition and Standardized Preparation of External Sonar Datasets.

Fetches genuine acoustic sonar data for canonical classes lacking coverage:
  - Class 0: derelict_fishing_gear (NKSID Oculus M750d FLS fishing_net)
  - Class 2: shipwreck (KLSG Klein 3000 SSS wreck)
  - Class 3: pipe_or_cylinder (ARIS Explorer 3000 FLS plastic-pipe + NKSID FLS cylinder)

Standardizes images to 640x640 letterboxed acoustic images, generates standard
YOLO detection annotations, and outputs a complete DATASET_MANIFEST.json and
provenance.jsonl ledger.
"""

import os
import sys
import json
import time
import zipfile
import io
import shutil
import hashlib
import subprocess
import urllib.request
from pathlib import Path
from typing import Dict, List, Tuple, Any

import cv2
import numpy as np

# Canonical taxonomy mapping
CANONICAL_CLASSES = {
    0: "derelict_fishing_gear",
    1: "general_marine_debris",
    2: "shipwreck",
    3: "pipe_or_cylinder",
    4: "other_man_made_target"
}

SOURCES_INFO = {
    "nksid_fishing_net": {
        "class_id": 0,
        "class_name": "derelict_fishing_gear",
        "url": "https://raw.githubusercontent.com/Jorwnpay/NK-Sonar-Image-Dataset/main/NKSID/fishing_net.zip",
        "institution": "Nankai University",
        "authors": ["Wenpei Jiao", "Jianlei Zhang", "Chunyan Zhang"],
        "publication": "Open-set recognition with long-tail sonar images (Elsevier ESWA 2024)",
        "sensor": "Oculus M750d Multi-beam Forward-Looking Sonar (1.2 MHz)",
        "modality": "FLS",
        "license": "MIT",
        "archive_type": "zip"
    },
    "klsg_wreck": {
        "class_id": 2,
        "class_name": "shipwreck",
        "url": "https://raw.githubusercontent.com/Jorwnpay/TGRS_BETL/main/data/KLSG/wreck.rar",
        "institution": "Hohai University / Ocean University of China",
        "authors": ["Guanying Huo", "Zhengxian Yang", "Wenpei Jiao"],
        "publication": "Underwater object classification in sidescan sonar images (IEEE TGRS 2020/2022)",
        "sensor": "Klein 3000 Side-Scan Sonar Towfish (455 kHz / 900 kHz)",
        "modality": "SSS",
        "license": "MIT",
        "archive_type": "rar"
    },
    "turntable_plastic_pipe": {
        "class_id": 3,
        "class_name": "pipe_or_cylinder",
        "base_url": "https://raw.githubusercontent.com/mvaldenegro/marine-debris-fls-datasets/master/md_fls_dataset/data/turntable-cropped/plastic-pipe",
        "institution": "University of Groningen / Heriot-Watt University",
        "authors": ["Dr. Matias Valdenegro-Toro"],
        "publication": "Marine Debris Detection with Forward-Looking Sonar (IEEE AUV 2020)",
        "doi": "10.5281/zenodo.15101686",
        "sensor": "Sound Metrics ARIS Explorer 3000 (3.0 MHz)",
        "modality": "FLS",
        "license": "CC-BY 4.0",
        "archive_type": "direct_png"
    },
    "nksid_cylinder": {
        "class_id": 3,
        "class_name": "pipe_or_cylinder",
        "url": "https://raw.githubusercontent.com/Jorwnpay/NK-Sonar-Image-Dataset/main/NKSID/cylinder.zip",
        "institution": "Nankai University",
        "authors": ["Wenpei Jiao", "Jianlei Zhang", "Chunyan Zhang"],
        "publication": "Open-set recognition with long-tail sonar images (Elsevier ESWA 2024)",
        "sensor": "Oculus M750d Multi-beam Forward-Looking Sonar (1.2 MHz)",
        "modality": "FLS",
        "license": "MIT",
        "archive_type": "zip"
    }
}


def letterbox_image(img: np.ndarray, target_size: int = 640) -> Tuple[np.ndarray, float, int, int]:
    """Pad and resize image to target_size square canvas while maintaining aspect ratio."""
    h, w = img.shape[:2]
    scale = min(target_size / h, target_size / w)
    nw, nh = int(round(w * scale)), int(round(h * scale))
    
    resized = cv2.resize(img, (nw, nh), interpolation=cv2.INTER_LINEAR)
    
    # Create canvas
    if len(img.shape) == 3:
        canvas = np.zeros((target_size, target_size, 3), dtype=np.uint8)
    else:
        canvas = np.zeros((target_size, target_size), dtype=np.uint8)
        
    pad_top = (target_size - nh) // 2
    pad_left = (target_size - nw) // 2
    
    canvas[pad_top:pad_top + nh, pad_left:pad_left + nw] = resized
    return canvas, scale, pad_top, pad_left


def compute_object_bbox(img_crop: np.ndarray) -> Tuple[float, float, float, float]:
    """Estimate object bounding box within acoustic crop using intensity thresholding."""
    if len(img_crop.shape) == 3:
        gray = cv2.cvtColor(img_crop, cv2.COLOR_BGR2GRAY)
    else:
        gray = img_crop.copy()
        
    h, w = gray.shape[:2]
    # Otsu or mean threshold
    thresh_val = max(30, int(np.mean(gray) + 0.5 * np.std(gray)))
    _, mask = cv2.threshold(gray, thresh_val, 255, cv2.THRESH_BINARY)
    
    # Morphological clean
    kernel = np.ones((3, 3), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if contours:
        # Find largest contour
        c = max(contours, key=cv2.contourArea)
        bx, by, bw, bh = cv2.boundingRect(c)
        # Margin
        margin_x = int(bw * 0.1)
        margin_y = int(bh * 0.1)
        x1 = max(0, bx - margin_x)
        y1 = max(0, by - margin_y)
        x2 = min(w, bx + bw + margin_x)
        y2 = min(h, by + bh + margin_y)
        return float(x1), float(y1), float(x2 - x1), float(y2 - y1)
    
    # Fallback to central 80% if no bright acoustic region detected
    x1, y1 = 0.1 * w, 0.1 * h
    bw, bh = 0.8 * w, 0.8 * h
    return float(x1), float(y1), float(bw), float(bh)


def acquire_dataset(output_dir: Path, max_samples_per_class: int = 100) -> Dict[str, Any]:
    """Acquire and process canonical evaluation dataset."""
    output_dir.mkdir(parents=True, exist_ok=True)
    images_dir = output_dir / "images"
    labels_dir = output_dir / "labels"
    raw_cache_dir = output_dir / "raw_cache"
    meta_dir = output_dir / "metadata"
    
    images_dir.mkdir(parents=True, exist_ok=True)
    labels_dir.mkdir(parents=True, exist_ok=True)
    raw_cache_dir.mkdir(parents=True, exist_ok=True)
    meta_dir.mkdir(parents=True, exist_ok=True)
    
    provenance_records = []
    manifest_records = []
    class_counts = {k: 0 for k in CANONICAL_CLASSES.keys()}
    
    print("=" * 60)
    print("ACQUIRING EXTERNAL CANONICAL SONAR BENCHMARK ASSETS")
    print("=" * 60)

    # 1. Class 0: NKSID fishing_net
    src_info = SOURCES_INFO["nksid_fishing_net"]
    print(f"\n[1/4] Fetching {src_info['class_name']} from NKSID...")
    net_zip_path = raw_cache_dir / "fishing_net.zip"
    if not net_zip_path.exists() or net_zip_path.stat().st_size == 0:
        urllib.request.urlretrieve(src_info["url"], net_zip_path)
    
    with zipfile.ZipFile(net_zip_path, 'r') as z:
        img_names = [f for f in z.namelist() if f.lower().endswith(('.jpg', '.png'))]
        for name in img_names[:max_samples_per_class]:
            raw_bytes = z.read(name)
            arr = np.frombuffer(raw_bytes, np.uint8)
            img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
            if img is None:
                continue
            
            # Crop bbox before letterbox
            orig_h, orig_w = img.shape[:2]
            bx, by, bw, bh = compute_object_bbox(img)
            
            # Letterbox to 640x640
            canvas, scale, pad_top, pad_left = letterbox_image(img, 640)
            
            # Map bbox to letterbox canvas
            new_bx = bx * scale + pad_left
            new_by = by * scale + pad_top
            new_bw = bw * scale
            new_bh = bh * scale
            
            # YOLO normalized format: x_center, y_center, w, h
            xc = (new_bx + new_bw / 2.0) / 640.0
            yc = (new_by + new_bh / 2.0) / 640.0
            nw = new_bw / 640.0
            nh = new_bh / 640.0
            
            out_name = f"ext_cls0_nksid_net_{Path(name).stem}.png"
            out_img_path = images_dir / out_name
            out_lbl_path = labels_dir / f"{Path(out_name).stem}.txt"
            
            cv2.imwrite(str(out_img_path), canvas)
            with open(out_lbl_path, "w") as lf:
                lf.write(f"0 {xc:.6f} {yc:.6f} {nw:.6f} {nh:.6f}\n")
                
            img_hash = hashlib.sha256(open(out_img_path, 'rb').read()).hexdigest()
            class_counts[0] += 1
            manifest_records.append({
                "filename": out_name,
                "class_id": 0,
                "class_name": "derelict_fishing_gear",
                "source": "NKSID",
                "sensor": src_info["sensor"],
                "modality": src_info["modality"],
                "sha256": img_hash
            })
            provenance_records.append({
                "filename": out_name,
                "class_id": 0,
                "source_dataset": "NKSID (NanKai Sonar Image Dataset)",
                "institution": src_info["institution"],
                "authors": src_info["authors"],
                "publication": src_info["publication"],
                "license": src_info["license"],
                "sensor": src_info["sensor"],
                "modality": src_info["modality"],
                "sha256": img_hash
            })
    print(f"-> Integrated {class_counts[0]} derelict_fishing_gear FLS images.")

    # 2. Class 2: KLSG wreck
    src_info = SOURCES_INFO["klsg_wreck"]
    print(f"\n[2/4] Fetching {src_info['class_name']} from KLSG (TGRS BETL)...")
    wreck_rar_path = raw_cache_dir / "wreck.rar"
    if not wreck_rar_path.exists() or wreck_rar_path.stat().st_size == 0:
        urllib.request.urlretrieve(src_info["url"], wreck_rar_path)
        
    wreck_extract_dir = raw_cache_dir / "extracted_wreck"
    wreck_extract_dir.mkdir(parents=True, exist_ok=True)
    
    # Extract using tar (bsdtar)
    cmd = ["tar", "-xf", str(wreck_rar_path), "-C", str(wreck_extract_dir)]
    subprocess.run(cmd, check=True)
    
    wreck_files = sorted(list(wreck_extract_dir.glob("**/*.png")) + list(wreck_extract_dir.glob("**/*.jpg")))
    for idx, wpath in enumerate(wreck_files[:max_samples_per_class]):
        img = cv2.imread(str(wpath))
        if img is None:
            continue
            
        orig_h, orig_w = img.shape[:2]
        bx, by, bw, bh = compute_object_bbox(img)
        canvas, scale, pad_top, pad_left = letterbox_image(img, 640)
        
        new_bx = bx * scale + pad_left
        new_by = by * scale + pad_top
        new_bw = bw * scale
        new_bh = bh * scale
        
        xc = (new_bx + new_bw / 2.0) / 640.0
        yc = (new_by + new_bh / 2.0) / 640.0
        nw = new_bw / 640.0
        nh = new_bh / 640.0
        
        out_name = f"ext_cls2_klsg_wreck_{wpath.stem}.png"
        out_img_path = images_dir / out_name
        out_lbl_path = labels_dir / f"{Path(out_name).stem}.txt"
        
        cv2.imwrite(str(out_img_path), canvas)
        with open(out_lbl_path, "w") as lf:
            lf.write(f"2 {xc:.6f} {yc:.6f} {nw:.6f} {nh:.6f}\n")
            
        img_hash = hashlib.sha256(open(out_img_path, 'rb').read()).hexdigest()
        class_counts[2] += 1
        manifest_records.append({
            "filename": out_name,
            "class_id": 2,
            "class_name": "shipwreck",
            "source": "KLSG",
            "sensor": src_info["sensor"],
            "modality": src_info["modality"],
            "sha256": img_hash
        })
        provenance_records.append({
            "filename": out_name,
            "class_id": 2,
            "source_dataset": "KLSG (Sidescan Sonar Dataset)",
            "institution": src_info["institution"],
            "authors": src_info["authors"],
            "publication": src_info["publication"],
            "license": src_info["license"],
            "sensor": src_info["sensor"],
            "modality": src_info["modality"],
            "sha256": img_hash
        })
    print(f"-> Integrated {class_counts[2]} shipwreck SSS images.")

    # 3. Class 3: Valdenegro-Toro Turntable plastic-pipe
    src_info = SOURCES_INFO["turntable_plastic_pipe"]
    print(f"\n[3/4] Fetching {src_info['class_name']} from Valdenegro-Toro Turntable FLS benchmark...")
    # Fetch 50 frames
    pipe_samples = min(50, max_samples_per_class // 2)
    turntable_count = 0
    for i in range(pipe_samples):
        frame_idx = i * 4  # sample every 4 frames for angular diversity across 360 deg
        img_name = f"object-sideways-frame-{frame_idx:03d}.png"
        url = f"{src_info['base_url']}/{img_name}"
        cache_file = raw_cache_dir / f"turntable_{img_name}"
        
        try:
            if not cache_file.exists():
                urllib.request.urlretrieve(url, cache_file)
            img = cv2.imread(str(cache_file))
            if img is None:
                continue
                
            orig_h, orig_w = img.shape[:2]
            bx, by, bw, bh = compute_object_bbox(img)
            canvas, scale, pad_top, pad_left = letterbox_image(img, 640)
            
            new_bx = bx * scale + pad_left
            new_by = by * scale + pad_top
            new_bw = bw * scale
            new_bh = bh * scale
            
            xc = (new_bx + new_bw / 2.0) / 640.0
            yc = (new_by + new_bh / 2.0) / 640.0
            nw = new_bw / 640.0
            nh = new_bh / 640.0
            
            out_name = f"ext_cls3_turntable_pipe_{frame_idx:03d}.png"
            out_img_path = images_dir / out_name
            out_lbl_path = labels_dir / f"{Path(out_name).stem}.txt"
            
            cv2.imwrite(str(out_img_path), canvas)
            with open(out_lbl_path, "w") as lf:
                lf.write(f"3 {xc:.6f} {yc:.6f} {nw:.6f} {nh:.6f}\n")
                
            img_hash = hashlib.sha256(open(out_img_path, 'rb').read()).hexdigest()
            class_counts[3] += 1
            turntable_count += 1
            manifest_records.append({
                "filename": out_name,
                "class_id": 3,
                "class_name": "pipe_or_cylinder",
                "source": "Turntable FLS",
                "sensor": src_info["sensor"],
                "modality": src_info["modality"],
                "sha256": img_hash
            })
            provenance_records.append({
                "filename": out_name,
                "class_id": 3,
                "source_dataset": "Marine Debris FLS Benchmark (Turntable Cropped)",
                "institution": src_info["institution"],
                "authors": src_info["authors"],
                "publication": src_info["publication"],
                "doi": src_info.get("doi"),
                "license": src_info["license"],
                "sensor": src_info["sensor"],
                "modality": src_info["modality"],
                "sha256": img_hash
            })
        except Exception as e:
            print(f"Warning: skipped {img_name}: {e}")
            continue
    print(f"-> Integrated {turntable_count} plastic-pipe ARIS 3000 FLS images.")

    # 4. Class 3: NKSID cylinder (FLS)
    src_info = SOURCES_INFO["nksid_cylinder"]
    print(f"\n[4/4] Fetching {src_info['class_name']} from NKSID cylinder...")
    cyl_zip_path = raw_cache_dir / "cylinder.zip"
    if not cyl_zip_path.exists() or cyl_zip_path.stat().st_size == 0:
        urllib.request.urlretrieve(src_info["url"], cyl_zip_path)
        
    nksid_cyl_count = 0
    with zipfile.ZipFile(cyl_zip_path, 'r') as z:
        img_names = [f for f in z.namelist() if f.lower().endswith(('.jpg', '.png'))]
        for name in img_names[:50]:
            raw_bytes = z.read(name)
            arr = np.frombuffer(raw_bytes, np.uint8)
            img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
            if img is None:
                continue
                
            orig_h, orig_w = img.shape[:2]
            bx, by, bw, bh = compute_object_bbox(img)
            canvas, scale, pad_top, pad_left = letterbox_image(img, 640)
            
            new_bx = bx * scale + pad_left
            new_by = by * scale + pad_top
            new_bw = bw * scale
            new_bh = bh * scale
            
            xc = (new_bx + new_bw / 2.0) / 640.0
            yc = (new_by + new_bh / 2.0) / 640.0
            nw = new_bw / 640.0
            nh = new_bh / 640.0
            
            out_name = f"ext_cls3_nksid_cyl_{Path(name).stem}.png"
            out_img_path = images_dir / out_name
            out_lbl_path = labels_dir / f"{Path(out_name).stem}.txt"
            
            cv2.imwrite(str(out_img_path), canvas)
            with open(out_lbl_path, "w") as lf:
                lf.write(f"3 {xc:.6f} {yc:.6f} {nw:.6f} {nh:.6f}\n")
                
            img_hash = hashlib.sha256(open(out_img_path, 'rb').read()).hexdigest()
            class_counts[3] += 1
            nksid_cyl_count += 1
            manifest_records.append({
                "filename": out_name,
                "class_id": 3,
                "class_name": "pipe_or_cylinder",
                "source": "NKSID Cylinder",
                "sensor": src_info["sensor"],
                "modality": src_info["modality"],
                "sha256": img_hash
            })
            provenance_records.append({
                "filename": out_name,
                "class_id": 3,
                "source_dataset": "NKSID (NanKai Sonar Image Dataset)",
                "institution": src_info["institution"],
                "authors": src_info["authors"],
                "publication": src_info["publication"],
                "license": src_info["license"],
                "sensor": src_info["sensor"],
                "modality": src_info["modality"],
                "sha256": img_hash
            })
    print(f"-> Integrated {nksid_cyl_count} cylinder Oculus FLS images.")

    # Write data.yaml
    data_yaml_content = f"""# Canonical Evaluation Benchmark Configuration
path: {output_dir.resolve().as_posix()}
train: images
val: images
test: images

names:
  0: derelict_fishing_gear
  1: general_marine_debris
  2: shipwreck
  3: pipe_or_cylinder
  4: other_man_made_target
"""
    with open(output_dir / "data.yaml", "w", encoding="utf-8") as f:
        f.write(data_yaml_content)
        
    # Write provenance.jsonl
    prov_file = meta_dir / "provenance.jsonl"
    with open(prov_file, "w", encoding="utf-8") as f:
        for r in provenance_records:
            f.write(json.dumps(r) + "\n")
            
    # Write DATASET_MANIFEST.json
    manifest = {
        "dataset_name": "canonical_evaluation_benchmark",
        "version": "1.0.0",
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "total_images": len(manifest_records),
        "total_annotations": len(manifest_records),
        "class_distribution": {
            f"{cid}_{CANONICAL_CLASSES[cid]}": count for cid, count in class_counts.items()
        },
        "modality_breakdown": {
            "FLS": sum(1 for m in manifest_records if m["modality"] == "FLS"),
            "SSS": sum(1 for m in manifest_records if m["modality"] == "SSS")
        },
        "sources": [
            {
                "source_name": "NKSID (fishing_net, cylinder)",
                "modality": "FLS",
                "sensor": "Oculus M750d (1.2 MHz)",
                "license": "MIT",
                "images": class_counts[0] + nksid_cyl_count
            },
            {
                "source_name": "KLSG (wreck)",
                "modality": "SSS",
                "sensor": "Klein 3000 Towfish (455/900 kHz)",
                "license": "MIT",
                "images": class_counts[2]
            },
            {
                "source_name": "Turntable (plastic-pipe)",
                "modality": "FLS",
                "sensor": "ARIS Explorer 3000 (3.0 MHz)",
                "license": "CC-BY 4.0",
                "images": turntable_count
            }
        ],
        "images": manifest_records
    }
    with open(output_dir / "DATASET_MANIFEST.json", "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
        
    print("\n" + "=" * 60)
    print(f"CANONICAL EVALUATION BENCHMARK PREPARED SUCCESSFULLY")
    print(f"Total Images: {len(manifest_records)}")
    print(f"Class 0 (derelict_fishing_gear): {class_counts[0]} (FLS)")
    print(f"Class 2 (shipwreck):             {class_counts[2]} (SSS)")
    print(f"Class 3 (pipe_or_cylinder):       {class_counts[3]} (FLS: {turntable_count} ARIS + {nksid_cyl_count} Oculus)")
    print("=" * 60)
    return manifest


if __name__ == "__main__":
    base_dir = Path(__file__).resolve().parent.parent
    target_out = base_dir / "datasets" / "canonical_evaluation"
    acquire_dataset(target_out, max_samples_per_class=100)
