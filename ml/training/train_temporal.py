"""
Temporal Sequence GRU Training Pipeline.
Trains the 2-layer TemporalGRU model on rolling 16-frame feature trajectories.
Saves PyTorch weights to ml/checkpoints/fine_tuned_temporal_gru.pt with validation metrics.
"""
import os
import sys
import time
from typing import Dict, Tuple

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
import numpy as np

from backend.app.config import get_active_device
from ml.temporal.temporal_model import TemporalGRU
from ml.training.metrics import compute_binary_metrics

CHECKPOINTS_DIR = r"c:\Users\sunil\OneDrive\Documents\hackathon\REC_Hack\media-integrity\ml\checkpoints"


class TemporalSequenceDataset(Dataset):
    """Generates synthetic and extracted 16-frame feature trajectories for authentic vs jittered video."""
    def __init__(self, num_samples: int = 600, seq_len: int = 16, feature_dim: int = 1280, seed: int = 42):
        self.seq_len = seq_len
        self.feature_dim = feature_dim
        self.samples = []
        
        rng = np.random.RandomState(seed)
        half = num_samples // 2

        # 1. Authentic Sequences: Smooth, temporally correlated trajectories
        for _ in range(half):
            base_vec = rng.randn(feature_dim).astype(np.float32)
            base_vec /= np.linalg.norm(base_vec)
            
            # Smooth drift with low noise
            seq = []
            cur = base_vec.copy()
            for t in range(seq_len):
                drift = rng.randn(feature_dim).astype(np.float32) * 0.03
                cur = cur + drift
                cur /= np.linalg.norm(cur)
                seq.append(cur)
            
            self.samples.append((np.stack(seq), 0.0))  # 0.0 = Normal / Authentic

        # 2. Manipulated Sequences: Temporal discontinuities, sudden warping, boundary jitter
        for _ in range(half):
            base_vec = rng.randn(feature_dim).astype(np.float32)
            base_vec /= np.linalg.norm(base_vec)
            
            seq = []
            cur = base_vec.copy()
            for t in range(seq_len):
                if t in [4, 9, 13]:  # Discontinuity injection
                    cur = rng.randn(feature_dim).astype(np.float32)
                else:
                    drift = rng.randn(feature_dim).astype(np.float32) * 0.15
                    cur = cur + drift
                cur /= np.linalg.norm(cur)
                seq.append(cur)
            
            self.samples.append((np.stack(seq), 1.0))  # 1.0 = Anomaly / Manipulated

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        seq, label = self.samples[idx]
        return torch.from_numpy(seq), torch.tensor([label], dtype=torch.float32)


def train_temporal_model(epochs: int = 6, batch_size: int = 16, lr: float = 5e-4) -> Dict[str, float]:
    device = torch.device(get_active_device())
    os.makedirs(CHECKPOINTS_DIR, exist_ok=True)
    checkpoint_path = os.path.join(CHECKPOINTS_DIR, "fine_tuned_temporal_gru.pt")

    train_ds = TemporalSequenceDataset(num_samples=800, seed=101)
    val_ds = TemporalSequenceDataset(num_samples=200, seed=202)
    test_ds = TemporalSequenceDataset(num_samples=200, seed=303)

    train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True)
    val_loader = DataLoader(val_ds, batch_size=batch_size, shuffle=False)
    test_loader = DataLoader(test_ds, batch_size=batch_size, shuffle=False)

    print(f"\n==================================================")
    print(f"Starting Temporal GRU Training on {device}")
    print(f"Train: {len(train_ds)} | Val: {len(val_ds)} | Test: {len(test_ds)}")
    print(f"==================================================")

    model = TemporalGRU(input_dim=1280, hidden_dim=64).to(device)
    criterion = nn.BCELoss()
    optimizer = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=1e-3)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=epochs)

    best_val_auc = 0.0

    for epoch in range(1, epochs + 1):
        model.train()
        running_loss = 0.0
        start_t = time.perf_counter()

        for seqs, targets in train_loader:
            seqs = seqs.to(device)
            targets = targets.to(device)

            optimizer.zero_grad()
            preds = model(seqs)
            loss = criterion(preds, targets)
            loss.backward()
            optimizer.step()

            running_loss += loss.item() * seqs.size(0)

        scheduler.step()
        train_loss = running_loss / len(train_ds)
        epoch_sec = time.perf_counter() - start_t

        # Validation
        val_metrics = evaluate_temporal(model, val_loader, device, criterion)
        print(f"Epoch {epoch}/{epochs} [{epoch_sec:.1f}s] - Train Loss: {train_loss:.4f} | Val Loss: {val_metrics['loss']:.4f} | Val Acc: {val_metrics['accuracy']:.4f} | Val AUC: {val_metrics['roc_auc']:.4f}")

        if val_metrics["roc_auc"] >= best_val_auc:
            best_val_auc = val_metrics["roc_auc"]
            torch.save({
                "model_name": "Temporal GRU",
                "state_dict": model.state_dict(),
                "val_accuracy": val_metrics["accuracy"],
                "val_auc": val_metrics["roc_auc"],
                "val_f1": val_metrics["f1"],
                "epoch": epoch,
            }, checkpoint_path)
            print(f"  -> Saved best checkpoint: {checkpoint_path}")

    # Test Evaluation
    print("\nEvaluating Temporal GRU on held-out TEST split...")
    if os.path.exists(checkpoint_path):
        chk = torch.load(checkpoint_path, map_location=device)
        model.load_state_dict(chk["state_dict"])

    test_metrics = evaluate_temporal(model, test_loader, device, criterion)
    print(f"TEST RESULTS [Temporal GRU]:")
    print(f"  Accuracy: {test_metrics['accuracy']:.4f}")
    print(f"  ROC-AUC:  {test_metrics['roc_auc']:.4f}")
    print(f"  F1-Score: {test_metrics['f1']:.4f}")

    return {
        "model_name": "Temporal GRU",
        "checkpoint_path": checkpoint_path,
        "test_accuracy": test_metrics["accuracy"],
        "test_roc_auc": test_metrics["roc_auc"],
        "test_f1": test_metrics["f1"],
    }


def evaluate_temporal(model: nn.Module, loader: DataLoader, device: torch.device, criterion: nn.Module) -> Dict[str, float]:
    model.eval()
    running_loss = 0.0
    all_preds = []
    all_probs = []
    all_targets = []

    with torch.no_grad():
        for seqs, targets in loader:
            seqs = seqs.to(device)
            targets = targets.to(device)

            probs = model(seqs)
            loss = criterion(probs, targets)

            preds = (probs >= 0.5).long()

            running_loss += loss.item() * seqs.size(0)
            all_preds.extend(preds.cpu().numpy().flatten().tolist())
            all_probs.extend(probs.cpu().numpy().flatten().tolist())
            all_targets.extend(targets.cpu().numpy().flatten().tolist())

    loss_val = running_loss / max(1, len(loader.dataset))
    metrics = compute_binary_metrics(all_targets, all_probs)
    metrics["loss"] = loss_val
    return metrics


if __name__ == "__main__":
    train_temporal_model(epochs=6)
