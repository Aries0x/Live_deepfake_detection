# Model Registry — Media Integrity / SecureCall

## Registry

| Model | Purpose | Source | Checkpoint | License | Input | Output | Device | Approx Latency | Status |
|-------|---------|--------|------------|---------|-------|--------|--------|----------------|--------|
| SCRFD-500M | Face detection | InsightFace | [insightface/SCRFD](https://github.com/deepinsight/insightface) | MIT (code) | BGR image (any size) | bboxes, confidences, keypoints (5-point) | cuda/cpu | ~5ms (GPU) | NOT_DOWNLOADED |
| EfficientNet-B0 | Visual deepfake detection (primary) | torchvision / custom | ImageNet pretrained + fine-tuned | Apache 2.0 (torchvision) | 224×224 RGB face crop | 2-class logits (real/fake) | cuda/cpu | ~8ms (GPU) | NOT_DOWNLOADED |
| EfficientNet-B4 | Visual deepfake detection (heavy) | torchvision / custom | ImageNet pretrained + fine-tuned | Apache 2.0 (torchvision) | 380×380 RGB face crop | 2-class logits (real/fake) | cuda/cpu | ~15ms (GPU) | NOT_DOWNLOADED |
| AASIST-L | Audio anti-spoofing | [clovaai/aasist](https://github.com/clovaai/aasist) | ASVspoof 2019 LA | MIT | 16kHz raw waveform (1s) | 2-class logits (bona-fide/spoof) | cuda/cpu | ~10ms (GPU) | NOT_DOWNLOADED |
| ArcFace | Identity embedding | InsightFace | [insightface/arcface](https://github.com/deepinsight/insightface) | MIT (code), LICENSE_REVIEW_REQUIRED (weights) | 112×112 aligned face | 512-d embedding | cuda/cpu | ~5ms (GPU) | NOT_DOWNLOADED |
| Temporal GRU | Temporal consistency | Custom | Trained from scratch | Project license | Sequence of frame embeddings (16 frames) | temporal_anomaly_score | cuda/cpu | ~2ms (GPU) | EXPERIMENTAL |
| SyncNet | A/V synchronization | [joonson/syncnet_python](https://github.com/joonson/syncnet_python) | Pre-trained | BSD-3-Clause | Mouth crops + MFCC features | sync offset + confidence | cuda/cpu | ~8ms (GPU) | NOT_DOWNLOADED |
| Grad-CAM | Visual attribution/heatmap | [jacobgil/pytorch-grad-cam](https://github.com/jacobgil/pytorch-grad-cam) | N/A (uses loaded model) | MIT | Model + input tensor + target layer | Heatmap (H×W) | cuda/cpu | ~3ms (GPU) | AVAILABLE |

## Status Definitions

| Status | Meaning |
|--------|---------|
| AVAILABLE | Model code and weights are ready to use |
| NOT_DOWNLOADED | Adapter implemented, weights need to be downloaded |
| LICENSE_REVIEW_REQUIRED | License terms need human review before use |
| CPU_ONLY | Model runs but only on CPU |
| CUDA_READY | Model tested and working on CUDA GPU |
| EXPERIMENTAL | Model is custom/in-development |

## Download Instructions

### SCRFD-500M
```bash
# Via insightface package
pip install insightface
# Weights auto-download on first use, or:
# Download from https://github.com/deepinsight/insightface/tree/master/detection/scrfd
```

### EfficientNet-B0/B4
```bash
# torchvision pretrained backbone
# Fine-tuned weights: train on FaceForensics++ or DFDC
# See training/ directory for training scripts
```

### AASIST-L
```bash
git clone https://github.com/clovaai/aasist.git
# Download checkpoint from the repository releases
# Place in models/aasist/
```

### ArcFace
```bash
pip install insightface
# Or download from https://github.com/deepinsight/insightface/tree/master/recognition/arcface_torch
```

### SyncNet
```bash
git clone https://github.com/joonson/syncnet_python.git
# Download pre-trained model
# Place in models/syncnet/
```

## Citations

### SCRFD
> Guo, J., Deng, J., Lattas, A., & Zafeiriou, S. (2021). Sample and Computation Redistribution for Efficient Face Detection. arXiv:2105.04714.

### EfficientNet
> Tan, M., & Le, Q. V. (2019). EfficientNet: Rethinking Model Scaling for Convolutional Neural Networks. ICML 2019.

### AASIST
> Jung, J., Heo, H., Tak, H., Shim, H., Chung, J. S., Lee, B., Yu, H., & Shinoda, K. (2022). AASIST: Audio Anti-Spoofing using Integrated Spectro-Temporal Graph Attention Networks. ICASSP 2022.

### ArcFace
> Deng, J., Guo, J., Xue, N., & Zafeiriou, S. (2019). ArcFace: Additive Angular Margin Loss for Deep Face Recognition. CVPR 2019.

### SyncNet
> Chung, J. S., & Zisserman, A. (2016). Out of time: automated lip sync in the wild. ACCV 2016.

## Commercial Redistribution

| Model | Commercial Use Allowed | Notes |
|-------|----------------------|-------|
| SCRFD | Yes (MIT code) | Weight license may differ — review |
| EfficientNet | Yes (Apache 2.0) | Fine-tuned weights inherit training data license |
| AASIST | Yes (MIT) | Check ASVspoof dataset terms separately |
| ArcFace | LICENSE_REVIEW_REQUIRED | Weights may have restrictions |
| SyncNet | Yes (BSD-3) | Check pre-trained weight terms |
| Grad-CAM | Yes (MIT) | Library only, no separate weights |
