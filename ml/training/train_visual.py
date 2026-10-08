"""
Visual Models Fine-Tuning Pipeline (EfficientNet-B0 + ViT-B/16).
Fine-tunes both models on extracted FaceForensics++ face crops.
Saves PyTorch weights to ml/checkpoints/ with validation metrics and ROC-AUC.
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
from torchvision import transforms, models
from PIL import Image
import numpy as np

from backend.app.config import get_active_device
from ml.training.metrics import compute_binary_metrics

DATA_DIR = r"c:\Users\sunil\OneDrive\Documents\hackathon\REC_Hack\media-integrity\data\extracted\video"
CHECKPOINTS_DIR = r"c:\Users\sunil\OneDrive\Documents\hackathon\REC_Hack\media-integrity\ml\checkpoints"


class FaceCropDataset(Dataset):
    def __init__(self, split: str = "train", transform=None):
        self.samples = []
        self.transform = transform
        
        split_dir = os.path.join(DATA_DIR, split)
        real_dir = os.path.join(split_dir, "real")
        fake_dir = os.path.join(split_dir, "fake")

        if os.path.exists(real_dir):
            for fname in os.listdir(real_dir):
                if fname.lower().endswith((".jpg", ".png", ".jpeg")):
                    self.samples.append((os.path.join(real_dir, fname), 0))  # 0: Authentic/Real

        if os.path.exists(fake_dir):
            for fname in os.listdir(fake_dir):
                if fname.lower().endswith((".jpg", ".png", ".jpeg")):
                    self.samples.append((os.path.join(fake_dir, fname), 1))  # 1: Manipulated/Fake

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        path, label = self.samples[idx]
        image = Image.open(path).convert("RGB")
        if self.transform:
            image = self.transform(image)
        return image, torch.tensor(label, dtype=torch.long)


def get_data_loaders(batch_size: int = 16) -> Tuple[DataLoader, DataLoader, DataLoader]:
    train_transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.RandomHorizontalFlip(p=0.5),
        transforms.ColorJitter(brightness=0.1, contrast=0.1),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ])

    val_transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ])

    train_ds = FaceCropDataset("train", transform=train_transform)
    val_ds = FaceCropDataset("val", transform=val_transform)
    test_ds = FaceCropDataset("test", transform=val_transform)

    train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True, drop_last=False, num_workers=0)
    val_loader = DataLoader(val_ds, batch_size=batch_size, shuffle=False, num_workers=0)
    test_loader = DataLoader(test_ds, batch_size=batch_size, shuffle=False, num_workers=0)

    return train_loader, val_loader, test_loader


def train_single_model(
    model: nn.Module,
    model_name: str,
    train_loader: DataLoader,
    val_loader: DataLoader,
    test_loader: DataLoader,
    device: torch.device,
    epochs: int = 3,
    lr: float = 1e-4,
) -> Dict[str, float]:
    print(f"\n==================================================")
    print(f"Starting Fine-Tuning: {model_name} on {device}")
    print(f"Train samples: {len(train_loader.dataset)} | Val: {len(val_loader.dataset)} | Test: {len(test_loader.dataset)}")
    print(f"==================================================")

    model.to(device)
    criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=1e-3)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=epochs)
    scaler = torch.cuda.amp.GradScaler(enabled=(device.type == "cuda"))

    best_val_auc = 0.0
    best_weights_path = os.path.join(CHECKPOINTS_DIR, f"fine_tuned_{model_name.lower().replace('-', '_').replace('/', '_')}.pt")
    os.makedirs(CHECKPOINTS_DIR, exist_ok=True)

    for epoch in range(1, epochs + 1):
        model.train()
        running_loss = 0.0
        start_t = time.perf_counter()

        for images, labels in train_loader:
            images = images.to(device)
            labels = labels.to(device)

            optimizer.zero_grad()
            with torch.cuda.amp.autocast(enabled=(device.type == "cuda")):
                outputs = model(images)
                loss = criterion(outputs, labels)

            scaler.scale(loss).backward()
            scaler.step(optimizer)
            scaler.update()

            running_loss += loss.item() * images.size(0)

        scheduler.step()
        train_loss = running_loss / max(1, len(train_loader.dataset))
        epoch_sec = time.perf_counter() - start_t

        # Validation Step
        val_metrics = evaluate_model(model, val_loader, device, criterion)
        print(f"Epoch {epoch}/{epochs} [{epoch_sec:.1f}s] - Train Loss: {train_loss:.4f} | Val Loss: {val_metrics['loss']:.4f} | Val Acc: {val_metrics['accuracy']:.4f} | Val AUC: {val_metrics['roc_auc']:.4f}")

        if val_metrics["roc_auc"] >= best_val_auc:
            best_val_auc = val_metrics["roc_auc"]
            torch.save({
                "model_name": model_name,
                "state_dict": model.state_dict(),
                "val_accuracy": val_metrics["accuracy"],
                "val_auc": val_metrics["roc_auc"],
                "val_f1": val_metrics["f1"],
                "epoch": epoch,
            }, best_weights_path)
            print(f"  -> Saved best checkpoint: {best_weights_path}")

    # Final Test Set Evaluation
    print(f"\nEvaluating {model_name} on held-out TEST split...")
    if os.path.exists(best_weights_path):
        chk = torch.load(best_weights_path, map_location=device)
        model.load_state_dict(chk["state_dict"])
    
    test_metrics = evaluate_model(model, test_loader, device, criterion)
    print(f"TEST RESULTS [{model_name}]:")
    print(f"  Accuracy: {test_metrics['accuracy']:.4f}")
    print(f"  ROC-AUC:  {test_metrics['roc_auc']:.4f}")
    print(f"  F1-Score: {test_metrics['f1']:.4f}")

    return {
        "model_name": model_name,
        "checkpoint_path": best_weights_path,
        "test_accuracy": test_metrics["accuracy"],
        "test_roc_auc": test_metrics["roc_auc"],
        "test_f1": test_metrics["f1"],
    }


def evaluate_model(model: nn.Module, loader: DataLoader, device: torch.device, criterion: nn.Module) -> Dict[str, float]:
    model.eval()
    running_loss = 0.0
    all_preds = []
    all_probs = []
    all_targets = []

    with torch.no_grad():
        for images, labels in loader:
            images = images.to(device)
            labels = labels.to(device)

            with torch.cuda.amp.autocast(enabled=(device.type == "cuda")):
                outputs = model(images)
                loss = criterion(outputs, labels)

            probs = torch.softmax(outputs, dim=1)[:, 1]
            preds = torch.argmax(outputs, dim=1)

            running_loss += loss.item() * images.size(0)
            all_preds.extend(preds.cpu().numpy().tolist())
            all_probs.extend(probs.cpu().numpy().tolist())
            all_targets.extend(labels.cpu().numpy().tolist())

    total = max(1, len(loader.dataset))
    loss_val = running_loss / total

    metrics = compute_binary_metrics(all_targets, all_probs)
    metrics["loss"] = loss_val
    return metrics


def run_visual_finetuning(epochs: int = 4):
    device = torch.device(get_active_device())
    results = {}

    # 1. Fine-Tune EfficientNet-B0 (Batch size 32, Staged Unfreezing)
    print("\n>>> Model 1/2: Preparing EfficientNet-B0 Backbone (Staged Transfer Learning) <<<")
    eff_train_loader, eff_val_loader, eff_test_loader = get_data_loaders(batch_size=32)
    eff_model = models.efficientnet_b0(weights=models.EfficientNet_B0_Weights.DEFAULT)
    in_features = eff_model.classifier[1].in_features
    eff_model.classifier[1] = nn.Linear(in_features, 2)
    
    # Freeze stem + first 3 blocks to preserve universal low-level edge filters
    for i in range(4):
        for p in eff_model.features[i].parameters():
            p.requires_grad = False

    eff_results = train_single_model(
        model=eff_model,
        model_name="efficientnet_b0",
        train_loader=eff_train_loader,
        val_loader=eff_val_loader,
        test_loader=eff_test_loader,
        device=device,
        epochs=epochs,
        lr=2.5e-4,
    )
    results["efficientnet_b0"] = eff_results

    # 2. Fine-Tune Vision Transformer (ViT-B/16) (Batch size 16, Top 4 Layers + Head)
    print("\n>>> Model 2/2: Preparing Vision Transformer (ViT-B/16) Backbone <<<")
    vit_train_loader, vit_val_loader, vit_test_loader = get_data_loaders(batch_size=16)
    vit_model = models.vit_b_16(weights=models.ViT_B_16_Weights.DEFAULT)
    vit_in_features = vit_model.heads.head.in_features
    vit_model.heads.head = nn.Linear(vit_in_features, 2)

    # Freeze patch projection and first 8 transformer blocks
    for p in vit_model.conv_proj.parameters():
        p.requires_grad = False
    for i in range(8):
        for p in vit_model.encoder.layers[i].parameters():
            p.requires_grad = False

    vit_results = train_single_model(
        model=vit_model,
        model_name="vit_b16",
        train_loader=vit_train_loader,
        val_loader=vit_val_loader,
        test_loader=vit_test_loader,
        device=device,
        epochs=epochs,
        lr=6e-5,
    )
    results["vit_b16"] = vit_results

    return results


if __name__ == "__main__":
    run_visual_finetuning(epochs=3)
