# Experiment Reproducibility Guide

This guide provides deterministic step-by-step instructions to reproduce all dataset audits, baseline evaluations, acoustic augmentations, hard-negative mining runs, and promotion gate assessments in `MarineDebris-Sonar-AI`.

---

## 1. Environment & Setup

Ensure dependencies are installed and the working directory is repository root:
```powershell
# Verify Python environment
python --version
# Output: Python 3.14.x or 3.11.x

# Verify Ultralytics & PyTorch
python -c "import torch, ultralytics; print('Torch:', torch.__version__, 'Ultralytics:', ultralytics.__version__)"
```

---

## 2. Step-by-Step Reproduction Commands

### Step 2.1: Cryptographic Integrity Verification of Production Model
Verify that the production weights checkpoint has not been tampered with:
```powershell
python -c "import hashlib; h = hashlib.sha256(open('models/detection/sonar_yolov8_fls_trained.pt', 'rb').read()).hexdigest(); print('SHA256:', h); assert h == 'e1215c7e7f6e4f3722398bf93d975eb5013c49f78355d0d5f54ce982d495b3d7', 'HASH MISMATCH!'"
```

### Step 2.2: Full Dataset Audit & Leakage Verification
Run the comprehensive dataset and annotation auditor across V2 and V3:
```powershell
python scripts/datasets/run_dataset_audit.py
```
Outputs:
- Machine-readable manifest: `reports/dataset_audit_report.json`
- Documentation report: `docs/DATASET_AUDIT_REPORT.md`

### Step 2.3: True Baseline Reproduction
Reproduce the baseline metrics on legacy V2 and V3 held-out test splits:
```powershell
python backend/ml/evaluation/reproduce_frozen_benchmark.py
```
Outputs:
- Verified JSON metrics: `reports/evaluation_integrity/frozen_benchmark_reproduction.json`
- Baseline report: `docs/DETECTION_BASELINE_REPORT.md`

### Step 2.4: Hard-Negative Mining Pipeline
Run the false positive miner across negative survey sweeps:
```powershell
python -c "from pathlib import Path; from backend.ml.mining.hard_negative_miner import HardNegativeMiner; miner = HardNegativeMiner(conf_threshold=0.25); rep = miner.mine_negatives(Path('models/detection/sonar_yolov8_fls_trained.pt'), Path('datasets/sonar_debris_v3/hard_negatives')); print(rep.false_alarm_rate)"
```
Outputs:
- Mining report: `reports/hard_negative_mining/hard_negative_mining_report.json`
- Harvested false positive crops: `reports/hard_negative_mining/mined_fp_crops/`

### Step 2.5: Sonar-Aware Augmentation Validation
Verify that acoustic augmentations preserve bounding-box geometry and obey grazing-angle constraints:
```powershell
pytest tests/test_sonar_augmentor.py -v
```

### Step 2.6: Candidate Model Evaluation & Promotion Gate
Evaluate any candidate checkpoint against the 6 mandatory promotion gates:
```powershell
python -c "from pathlib import Path; from backend.ml.optimization.promotion_gate import PromotionGate; gate = PromotionGate(); res = gate.evaluate_checkpoint(Path('models/detection/experiments/phase3/P3_E2_NAIVE_MIX/weights/best.pt')); print('Status:', res.status); print('Passed:', res.overall_pass)"
```

---

## 3. Seed Control & Determinism
All controlled experiments and augmentations accept explicit seed parameters (`--seed 42`, `--seed 123`, `--seed 2026`). Ultrasonic PyTorch deterministic flags and seed pinning ensure bitwise reproducible splits and training trajectories.
