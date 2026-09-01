# MarineDebris-Sonar-AI: Model Training Pipeline

This directory contains the data preparation, augmentation, training, and evaluation infrastructure for training the YOLOv8m acoustic object detector.

---

## 1. Directory Structure

```
training/
├── augmentation/          # Acoustic-aware sonar data augmentation
│   └── sonar_augmentor.py # Speckle noise, gain variations, mirroring
├── configs/               # YOLO dataset YAML configurations
│   └── sonar_yolo_data.yaml.template
├── conversion/            # Annotation converters
│   ├── coco_to_yolo.py    # COCO JSON -> YOLO format converter
│   └── voc_to_yolo.py     # Pascal VOC XML -> YOLO format converter
├── evaluation/            # Model performance evaluator
│   └── evaluate_model.py  # mAP50, mAP50-95, precision, recall
└── training/              # Training runners
    └── train_yolo.py      # Ultralytics YOLOv8 runner with AdamW
```

---

## 2. Step-by-Step Training Workflow

### Step 1: Data Preparation & Conversion
Prepare Sidescan Sonar (SSS) images sliced to 640×640 tiles. If annotations are in COCO or VOC format, convert them using:
```bash
python training/conversion/coco_to_yolo.py --coco-path datasets/raw/annotations.json --output-dir datasets/sonar_debris/labels/train
```

### Step 2: Survey-Level Splitting (Prevent Data Leakage)
To prevent cross-tile data contamination:
- **Do not split randomly by image.** Tiles from the same survey track are highly correlated.
- **Split by survey track ID / session ID**: Assign entire surveys to either `train`, `val`, or `test`.

### Step 3: Dataset Configuration
Copy the template and configure your paths:
```bash
cp training/configs/sonar_yolo_data.yaml.template datasets/sonar_debris/data.yaml
```

### Step 4: Model Training
Launch Ultralytics YOLOv8m training with canonical hyperparameters:
```bash
python training/training/train_yolo.py \
    --data datasets/sonar_debris/data.yaml \
    --weights yolov8m.pt \
    --imgsz 640 \
    --batch 16 \
    --epochs 100 \
    --device 0
```
Upon completion, the best weights will be exported automatically to:
`models/detection/sonar_yolov8m_ghostpot_v1.pt`.

---

## 3. Acoustic Domain Hyperparameters
- **Input Size:** 640×640 pixels
- **Batch Size:** 16 (or 8 on 8GB VRAM)
- **Optimizer:** `AdamW` (initial learning rate `lr0=0.001`, weight decay `0.0005`)
- **Rotation Augmentation:** Disabled (`degrees=0.0`) to preserve acoustic shadow geometry (highlights always lead acoustic shadows relative to the sonar transducer).
- **Horizontal Flipping:** Enabled (`fliplr=0.5`) across the range axis.
