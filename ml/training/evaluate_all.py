"""
Comprehensive Evaluation & Calibration Benchmark for All Fine-Tuned Models.
Evaluates EfficientNet-B0, ViT-B/16, Parallel Ensemble, AASIST-L, and Temporal GRU
on the held-out TEST partitions.
Generates metrics JSON with accuracy, precision, recall, F1, ROC-AUC, and calibration.
"""
import os
import sys
import json
from typing import Dict, Any

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from torchvision import models, transforms
import numpy as np

from backend.app.config import get_active_device
from ml.training.metrics import compute_binary_metrics
from ml.training.train_visual import FaceCropDataset
from ml.training.train_audio import AcousticAudioDataset
from ml.training.train_temporal import TemporalSequenceDataset
from ml.audio.aasist_detector import AASISTLightNet
from ml.temporal.temporal_model import TemporalGRU

CHECKPOINTS_DIR = r"c:\Users\sunil\OneDrive\Documents\hackathon\REC_Hack\media-integrity\ml\checkpoints"
METRICS_JSON_PATH = os.path.join(CHECKPOINTS_DIR, "training_metrics.json")


def evaluate_visual_test(model: nn.Module, loader: DataLoader, device: torch.device) -> Dict[str, Any]:
    model.eval()
    all_probs, all_targets = [], []

    with torch.no_grad():
        for images, labels in loader:
            images = images.to(device)
            outputs = model(images)
            probs = torch.softmax(outputs, dim=1)[:, 1].cpu().numpy()

            all_probs.extend(probs.tolist())
            all_targets.extend(labels.numpy().tolist())

    metrics = compute_binary_metrics(all_targets, all_probs)
    metrics["test_samples"] = len(all_targets)
    return metrics


def evaluate_visual_ensemble_test(eff_model: nn.Module, vit_model: nn.Module, loader: DataLoader, device: torch.device) -> Dict[str, Any]:
    eff_model.eval()
    vit_model.eval()
    all_probs, all_targets = [], []

    with torch.no_grad():
        for images, labels in loader:
            images = images.to(device)
            eff_probs = torch.softmax(eff_model(images), dim=1)[:, 1].cpu().numpy()
            vit_probs = torch.softmax(vit_model(images), dim=1)[:, 1].cpu().numpy()

            # Weighted consensus (0.55 * eff + 0.45 * vit)
            ensemble_probs = 0.55 * eff_probs + 0.45 * vit_probs
            all_probs.extend(ensemble_probs.tolist())
            all_targets.extend(labels.numpy().tolist())

    metrics = compute_binary_metrics(all_targets, all_probs)
    metrics["test_samples"] = len(all_targets)
    return metrics


def evaluate_audio_test(model: nn.Module, loader: DataLoader, device: torch.device) -> Dict[str, Any]:
    model.eval()
    all_probs, all_targets = [], []

    with torch.no_grad():
        for specs, labels in loader:
            specs = specs.to(device)
            outputs = model(specs)
            probs = torch.softmax(outputs, dim=1)[:, 1].cpu().numpy()

            all_probs.extend(probs.tolist())
            all_targets.extend(labels.numpy().tolist())

    metrics = compute_binary_metrics(all_targets, all_probs)
    metrics["test_samples"] = len(all_targets)
    return metrics


def evaluate_temporal_test(model: nn.Module, loader: DataLoader, device: torch.device) -> Dict[str, Any]:
    model.eval()
    all_probs, all_targets = [], []

    with torch.no_grad():
        for seqs, targets in loader:
            seqs = seqs.to(device)
            probs = model(seqs).cpu().numpy().flatten()

            all_probs.extend(probs.tolist())
            all_targets.extend(targets.numpy().flatten().astype(int).tolist())

    metrics = compute_binary_metrics(all_targets, all_probs)
    metrics["test_samples"] = len(all_targets)
    return metrics


def evaluate_all():
    device = torch.device(get_active_device())
    metrics_summary = {}

    # 1. Visual Test Loader
    val_transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ])
    visual_test_ds = FaceCropDataset("test", transform=val_transform)
    visual_loader = DataLoader(visual_test_ds, batch_size=16, shuffle=False)

    # 2. Audio Test Loader
    audio_test_ds = AcousticAudioDataset("test")
    audio_loader = DataLoader(audio_test_ds, batch_size=16, shuffle=False)

    # 3. Temporal Test Loader
    temporal_test_ds = TemporalSequenceDataset(num_samples=200, seed=303)
    temporal_loader = DataLoader(temporal_test_ds, batch_size=16, shuffle=False)

    print("\n=======================================================")
    print(f"RUNNING COMPREHENSIVE BENCHMARK EVALUATION (CUDA={device})")
    print("=======================================================")

    # A. EfficientNet-B0
    eff_path = os.path.join(CHECKPOINTS_DIR, "fine_tuned_efficientnet_b0.pt")
    if os.path.exists(eff_path):
        print("Evaluating Fine-Tuned EfficientNet-B0...")
        eff_model = models.efficientnet_b0(weights=None)
        in_features = eff_model.classifier[1].in_features
        eff_model.classifier[1] = nn.Linear(in_features, 2)
        chk = torch.load(eff_path, map_location=device)
        eff_model.load_state_dict(chk["state_dict"])
        eff_model.to(device)
        metrics_summary["efficientnet_b0"] = evaluate_visual_test(eff_model, visual_loader, device)

    # B. ViT-B/16
    vit_path = os.path.join(CHECKPOINTS_DIR, "fine_tuned_vit_b16.pt")
    if os.path.exists(vit_path):
        print("Evaluating Fine-Tuned ViT-B/16...")
        vit_model = models.vit_b_16(weights=None)
        vit_in_features = vit_model.heads.head.in_features
        vit_model.heads.head = nn.Linear(vit_in_features, 2)
        chk = torch.load(vit_path, map_location=device)
        vit_model.load_state_dict(chk["state_dict"])
        vit_model.to(device)
        metrics_summary["vit_b16"] = evaluate_visual_test(vit_model, visual_loader, device)

    # C. Dual Ensemble
    if os.path.exists(eff_path) and os.path.exists(vit_path):
        print("Evaluating Parallel Visual Ensemble (EfficientNet-B0 + ViT-B/16)...")
        metrics_summary["parallel_visual_ensemble"] = evaluate_visual_ensemble_test(eff_model, vit_model, visual_loader, device)

    # D. AASIST-L
    aasist_path = os.path.join(CHECKPOINTS_DIR, "fine_tuned_aasist.pt")
    if os.path.exists(aasist_path):
        print("Evaluating Fine-Tuned AASIST-L...")
        audio_model = AASISTLightNet().to(device)
        chk = torch.load(aasist_path, map_location=device)
        audio_model.load_state_dict(chk["state_dict"])
        metrics_summary["aasist_l"] = evaluate_audio_test(audio_model, audio_loader, device)

    # E. Temporal GRU
    temp_path = os.path.join(CHECKPOINTS_DIR, "fine_tuned_temporal_gru.pt")
    if os.path.exists(temp_path):
        print("Evaluating Fine-Tuned Temporal GRU...")
        temp_model = TemporalGRU().to(device)
        chk = torch.load(temp_path, map_location=device)
        temp_model.load_state_dict(chk["state_dict"])
        metrics_summary["temporal_gru"] = evaluate_temporal_test(temp_model, temporal_loader, device)

    # Save summary
    with open(METRICS_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(metrics_summary, f, indent=2)

    print(f"\nAll benchmark metrics saved to -> {METRICS_JSON_PATH}")
    print(json.dumps(metrics_summary, indent=2))
    return metrics_summary


if __name__ == "__main__":
    evaluate_all()
