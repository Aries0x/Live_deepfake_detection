# Datasets — Media Integrity / SecureCall

## Research Datasets

| Dataset | Task | License | Train Split | Val Split | Test Split | Identity Separation |
|---------|------|---------|-------------|-----------|------------|-------------------|
| FaceForensics++ | Visual deepfake detection | Research-only (academic license required) | ~720 videos | ~140 videos | ~140 videos | By source video |
| DFDC | Visual deepfake detection | CC BY-NC 4.0 | ~100k videos | Provided | Provided | By source identity |
| ASVspoof 2019 LA | Audio anti-spoofing | CC BY 4.0 | ~25k utterances | ~24k utterances | ~71k utterances | By speaker |
| ASVspoof 2021 LA | Audio anti-spoofing | CC BY 4.0 | Inherited | Inherited | New eval set | By speaker |

## Critical Data Splitting Rules

1. **Split by source video / identity** — NEVER random frame sampling
2. Frames from the same source video must NEVER appear in both train and test
3. The training pipeline must FAIL or WARN if severe data leakage is detected
4. Track `source_video_id` and `identity_id` in all splits

## Data Leakage Prevention

The training pipeline includes a leakage detection check:
- Validates no overlap between train/test source video IDs
- Validates no overlap between train/test identity IDs
- Raises an error on >0% overlap

## Download Instructions

### FaceForensics++
- Request access at: https://github.com/ondyari/FaceForensics
- Requires academic affiliation
- Download via provided script after approval
- **Do NOT download without license approval**

### DFDC
- Available at: https://ai.meta.com/datasets/dfdc/
- Requires agreement to terms
- Large dataset (~470 GB)
- **Check storage requirements before download**

### ASVspoof
- Available at: https://www.asvspoof.org/
- CC BY 4.0 license
- Manageable size (~5 GB for LA partition)

## Storage Requirements

| Dataset | Approximate Size | Notes |
|---------|-----------------|-------|
| FaceForensics++ (c23) | ~30 GB | Compressed quality |
| FaceForensics++ (raw) | ~500 GB | Original quality |
| DFDC | ~470 GB | Full dataset |
| DFDC (subset) | ~50 GB | Preview subset |
| ASVspoof 2019 LA | ~5 GB | Audio only |

## Usage Notes

- These datasets are for **training and evaluation only**
- Do not redistribute dataset contents
- Models trained on these datasets inherit applicable license restrictions
- Always cite the original dataset papers in publications
