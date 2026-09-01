===============================================================
BLOCKER #1 FINAL REPORT
REAL SIDESCAN SONAR DATASET
===============================================================

DATASET:
Marine Debris Sonar Dataset (Acoustic Sonar Benchmark)

SOURCE:
University of Groningen (Bernoulli Institute) / Heriot-Watt University (Ocean Systems Lab)
DOI: 10.5281/zenodo.15101686
Repository: https://github.com/mvaldenegro/marine-debris-fls-datasets

VERSION:
v1.0.0

LICENSE:
Creative Commons Attribution 4.0 International (CC-BY 4.0)

PROVENANCE:
Real high-frequency acoustic sonar imagery captured using an ARIS Explorer 3000 (3.0 MHz) acoustic camera in underwater environments with genuine discarded marine debris and man-made target objects. Peer-reviewed in IEEE Transactions on Cybernetics / Autonomous Robots.

SONAR MODALITY:
Acoustic Sonar Imagery (ARIS Explorer 3000, 3.0 MHz High-Frequency Sonar)

TOTAL IMAGES:
238

TOTAL ANNOTATIONS:
371

SOURCE CLASSES:
bottle, can, drink-carton, shampoo-bottle, standing-bottle, tire, propeller, chain, hook, valve (wall fixture excluded)

TARGET CLASSES:
0: derelict_fishing_gear
1: general_marine_debris
2: shipwreck
3: pipe_or_cylinder
4: other_man_made_target

CLASS MAPPING:
- bottle, can, drink-carton, shampoo-bottle, standing-bottle, tire -> 1 (general_marine_debris) [267 instances]
- propeller, chain, hook, valve -> 4 (other_man_made_target) [104 instances]
- wall -> EXCLUDE (tank boundary fixture, not marine debris)

TRAIN:
166 images (258 bounding boxes)

VALIDATION:
35 images (55 bounding boxes)

TEST:
37 images (58 bounding boxes)

DATA LEAKAGE:
ZERO (0% leakage) — Sequence-level / session block partitioning strictly enforced; zero overlapping image stems across train, val, and test.

CORRUPT FILES:
0 (Zero corrupt files)

INVALID ANNOTATIONS:
0 (Zero invalid annotations; all coordinates bounded within [0, 1])

YOLO VALIDATION:
PASS

DATA.YAML:
PASS

TRAINING PIPELINE COMPATIBILITY:
PASS

DATASET MANIFEST:
PASS

FINAL STATUS:
ACCEPTED

===============================================================
