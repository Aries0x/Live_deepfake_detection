# ML Model Checkpoints

This directory contains evaluation metrics and fine-tuned model checkpoints for the SecureCall multimodal forensic pipeline.

## Checkpoints Overview

- `fine_tuned_efficientnet_b0.pt`: Fine-tuned visual manipulation classifier (EfficientNet-B0 backbone)
- `fine_tuned_vit_b16.pt`: Fine-tuned Vision Transformer (ViT-B/16 with spatial Grad-CAM attention)
- `fine_tuned_aasist.pt`: Fine-tuned AASIST-L voice anti-spoofing graph attention network
- `fine_tuned_temporal_gru.pt`: Bi-directional GRU temporal continuity model
- `training_metrics.json`: Empirical benchmark evaluation results across all models

> **Note**: Binary checkpoint files (`*.pt`) are excluded from Git version control due to GitHub repository size limits (>100MB). When checkpoints are absent, the inference engine falls back gracefully to torchvision/timm pretrained weights or synthetic forensic heuristics.

To train or reproduce the weights, run:
```bash
python -m ml.training.run_pipeline
```
