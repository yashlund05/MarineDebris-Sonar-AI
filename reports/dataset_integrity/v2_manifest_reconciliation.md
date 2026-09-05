# V2 Dataset Manifest Reconciliation Report

**Generated**: 2026-09-05T22:58:00Z  
**Status**: ✅ **RESOLVED**  
**Authoritative Source**: Filesystem label scan (cryptographically verifiable)

---

## Reconciliation Table

| Source | Train Img | Train Box | Val Img | Val Box | Test Img | Test Box | Total Img | Total Box | Status |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| **Filesystem scan** | 166 | 266 | 35 | 51 | 37 | 54 | 238 | 371 | ✅ GROUND TRUTH |
| **Phase 2.5 canonical** | 166 | 266 | 35 | 51 | 37 | 54 | 238 | 371 | ✅ AGREES |
| **Legacy DatasetPage.tsx** | 166 | 258 | 35 | 55 | 37 | 58 | 238 | 371 | ⚠️ INCORRECT per-split |
| **BENCHMARK_MANIFEST.json** | — | — | — | — | 37 | 54 | — | — | ✅ AGREES (test only) |

## Discrepancy Analysis

All three sources agree on image counts per split (166 / 35 / 37 = 238 total) and total annotations (371).

The **legacy DatasetPage.tsx** hardcoded values contain incorrect per-split annotation counts:
- Train: 258 (actual: **266**, Δ = -8)
- Val: 55 (actual: **51**, Δ = +4)
- Test: 58 (actual: **54**, Δ = +4)

These sum to 371, so the total was correct, but the per-split distribution was wrong.

The discrepancy likely originated from an early manual count or an outdated data processing step that was not updated when the clean V2 dataset was finalized.

## Resolution

| Decision | Value |
|---|---|
| Selected authoritative source | **Filesystem label file scan** |
| Reason | Label files are the ground-truth annotations. SHA256 hashes of all 238 image + 238 label files were computed and match the frozen baseline hashes in `frozen_baseline_hashes.json`. The Phase 2.5 user-stated canonical accounting agrees exactly with the filesystem scan. |
| Action | Generate `datasets/sonar_debris_v2_clean/DATASET_MANIFEST.json` using filesystem-scanned values |
| Legacy UI correction | The hardcoded values in `DatasetPage.tsx` (258/55/58) will be replaced by API-driven values (266/51/54) |

## Verified V2 Dataset Statistics

```
Split     Images   Annotations   Negatives   Class 1 (debris)   Class 4 (other)
train       166           266           0               195                71
val          35            51           0                25                26
test         37            54           0                47                 7
─────────────────────────────────────────────────────────────────────────────────
TOTAL       238           371           0               267               104
```

## Data Sources Checked

1. ✅ Filesystem image inventory (`datasets/sonar_debris_v2_clean/images/{train,val,test}/`)
2. ✅ Label files (`datasets/sonar_debris_v2_clean/labels/{train,val,test}/`)
3. ✅ `data.yaml` (class names, paths — no counts)
4. ✅ Train/val/test split definitions (directory-based)
5. ✅ Phase 2.5 evaluation artifacts (`BENCHMARK_MANIFEST.json`, `frozen_benchmark_reproduction.json`)
6. ✅ `frozen_baseline_hashes.json` (SHA256 of all files)
7. ❌ No existing `DATASET_MANIFEST.json` for V2 (will be generated)
8. ✅ Canonical benchmark manifests
