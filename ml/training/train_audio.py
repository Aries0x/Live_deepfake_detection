"""
Acoustic Anti-Spoofing (AASIST-L) Training Pipeline.
Trains the 2D-CNN + GRU network on extracted 16kHz speech audio samples.
Saves PyTorch weights to ml/checkpoints/fine_tuned_aasist.pt with validation metrics.
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
import torchaudio
import torchaudio.transforms as T
import soundfile as sf
import numpy as np

from backend.app.config import get_active_device
from ml.audio.aasist_detector import AASISTLightNet
from ml.training.metrics import compute_binary_metrics

DATA_DIR = r"c:\Users\sunil\OneDrive\Documents\hackathon\REC_Hack\media-integrity\data\extracted\audio"
CHECKPOINTS_DIR = r"c:\Users\sunil\OneDrive\Documents\hackathon\REC_Hack\media-integrity\ml\checkpoints"


class AcousticAudioDataset(Dataset):
    def __init__(self, split: str = "train", target_len_samples: int = 32000):
        self.samples = []
        self.target_len = target_len_samples
        self.mel_transform = T.MelSpectrogram(
            sample_rate=16000,
            n_fft=1024,
            win_length=512,
            hop_length=256,
            n_mels=64,
        )

        split_dir = os.path.join(DATA_DIR, split)
        gen_dir = os.path.join(split_dir, "genuine")
        spf_dir = os.path.join(split_dir, "spoofed")

        if os.path.exists(gen_dir):
            for fname in os.listdir(gen_dir):
                if fname.lower().endswith(".wav"):
                    self.samples.append((os.path.join(gen_dir, fname), 0))  # 0: Genuine speech

        if os.path.exists(spf_dir):
            for fname in os.listdir(spf_dir):
                if fname.lower().endswith(".wav"):
                    self.samples.append((os.path.join(spf_dir, fname), 1))  # 1: Spoofed / Cloned

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        path, label = self.samples[idx]
        wav_data, sr = sf.read(path)
        
        # Ensure 1D mono float32
        if wav_data.ndim > 1:
            wav_data = np.mean(wav_data, axis=1)
        wav_data = wav_data.astype(np.float32)

        # Pad or crop to target_len
        if len(wav_data) < self.target_len:
            pad = np.zeros(self.target_len - len(wav_data), dtype=np.float32)
            wav_data = np.concatenate([wav_data, pad])
        else:
            wav_data = wav_data[:self.target_len]

        t_wav = torch.from_numpy(wav_data).unsqueeze(0)  # (1, samples)
        mel_spec = self.mel_transform(t_wav)            # (1, 64, time_steps)
        # Log scale
        mel_spec = torch.log(mel_spec + 1e-6)

        return mel_spec, torch.tensor(label, dtype=torch.long)


def train_audio_model(epochs: int = 5, batch_size: int = 16, lr: float = 3e-4) -> Dict[str, float]:
    device = torch.device(get_active_device())
    os.makedirs(CHECKPOINTS_DIR, exist_ok=True)
    checkpoint_path = os.path.join(CHECKPOINTS_DIR, "fine_tuned_aasist.pt")

    train_ds = AcousticAudioDataset("train")
    val_ds = AcousticAudioDataset("val")
    test_ds = AcousticAudioDataset("test")

    train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True, num_workers=0)
    val_loader = DataLoader(val_ds, batch_size=batch_size, shuffle=False, num_workers=0)
    test_loader = DataLoader(test_ds, batch_size=batch_size, shuffle=False, num_workers=0)

    print(f"\n==================================================")
    print(f"Starting AASIST-L Acoustic Training on {device}")
    print(f"Train: {len(train_ds)} | Val: {len(val_ds)} | Test: {len(test_ds)}")
    print(f"==================================================")

    model = AASISTLightNet().to(device)
    criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=1e-4)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=epochs)

    best_val_auc = 0.0

    for epoch in range(1, epochs + 1):
        model.train()
        running_loss = 0.0
        start_t = time.perf_counter()

        for specs, labels in train_loader:
            specs = specs.to(device)
            labels = labels.to(device)

            optimizer.zero_grad()
            outputs = model(specs)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()

            running_loss += loss.item() * specs.size(0)

        scheduler.step()
        train_loss = running_loss / max(1, len(train_ds))
        epoch_sec = time.perf_counter() - start_t

        # Validation
        val_metrics = evaluate_audio(model, val_loader, device, criterion)
        print(f"Epoch {epoch}/{epochs} [{epoch_sec:.1f}s] - Train Loss: {train_loss:.4f} | Val Loss: {val_metrics['loss']:.4f} | Val Acc: {val_metrics['accuracy']:.4f} | Val AUC: {val_metrics['roc_auc']:.4f}")

        if val_metrics["roc_auc"] >= best_val_auc:
            best_val_auc = val_metrics["roc_auc"]
            torch.save({
                "model_name": "AASIST-L",
                "state_dict": model.state_dict(),
                "val_accuracy": val_metrics["accuracy"],
                "val_auc": val_metrics["roc_auc"],
                "val_f1": val_metrics["f1"],
                "epoch": epoch,
            }, checkpoint_path)
            print(f"  -> Saved best checkpoint: {checkpoint_path}")

    # Test Evaluation
    print("\nEvaluating AASIST-L on held-out TEST split...")
    if os.path.exists(checkpoint_path):
        chk = torch.load(checkpoint_path, map_location=device)
        model.load_state_dict(chk["state_dict"])

    test_metrics = evaluate_audio(model, test_loader, device, criterion)
    print(f"TEST RESULTS [AASIST-L]:")
    print(f"  Accuracy: {test_metrics['accuracy']:.4f}")
    print(f"  ROC-AUC:  {test_metrics['roc_auc']:.4f}")
    print(f"  F1-Score: {test_metrics['f1']:.4f}")

    return {
        "model_name": "AASIST-L",
        "checkpoint_path": checkpoint_path,
        "test_accuracy": test_metrics["accuracy"],
        "test_roc_auc": test_metrics["roc_auc"],
        "test_f1": test_metrics["f1"],
    }


def evaluate_audio(model: nn.Module, loader: DataLoader, device: torch.device, criterion: nn.Module) -> Dict[str, float]:
    model.eval()
    running_loss = 0.0
    all_preds = []
    all_probs = []
    all_targets = []

    with torch.no_grad():
        for specs, labels in loader:
            specs = specs.to(device)
            labels = labels.to(device)

            outputs = model(specs)
            loss = criterion(outputs, labels)

            probs = torch.softmax(outputs, dim=1)[:, 1]
            preds = torch.argmax(outputs, dim=1)

            running_loss += loss.item() * specs.size(0)
            all_preds.extend(preds.cpu().numpy().tolist())
            all_probs.extend(probs.cpu().numpy().tolist())
            all_targets.extend(labels.cpu().numpy().tolist())

    total = max(1, len(loader.dataset))
    loss_val = running_loss / total

    metrics = compute_binary_metrics(all_targets, all_probs)
    metrics["loss"] = loss_val
    return metrics


if __name__ == "__main__":
    train_audio_model(epochs=5)
