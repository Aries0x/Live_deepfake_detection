# Datasets

This directory contains documentation and scripts for dataset management.

**No datasets are stored in this repository.**

## Supported Datasets

See [../docs/datasets.md](../docs/datasets.md) for full documentation.

## Critical Rules

1. **Split by source video / identity** — NEVER random frame sampling
2. Frames from the same source video must NEVER appear in both train and test
3. The training pipeline must FAIL or WARN if severe data leakage is detected

## Directory Structure (after download)

```
datasets/
├── README.md
├── faceforensics/     # FaceForensics++ (requires license approval)
├── dfdc/              # DFDC (requires terms agreement)
├── asvspoof/          # ASVspoof 2019/2021 (CC BY 4.0)
└── scripts/
    ├── download_asvspoof.py
    └── validate_splits.py
```
