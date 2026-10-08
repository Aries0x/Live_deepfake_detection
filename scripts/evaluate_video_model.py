"""
Pure PyTorch/Python evaluation script for the video fusion & temporal transformer model.
Evaluates accuracy, precision, recall, F1, and per-category breakdown
using the FaceForensics++ benchmark embeddings in data/embeddings.
"""
import os
import time
import torch
import torch.nn as nn

class PositionalEncoding(nn.Module):
    def __init__(self, max_len=1000, d_model=512):
        super().__init__()
        self.pos_embed = nn.Embedding(max_len, d_model)

    def forward(self, x):
        seq_len = x.size(1)
        positions = torch.arange(seq_len, device=x.device).unsqueeze(0)
        return x + self.pos_embed(positions)

class TemporalModel(nn.Module):
    def __init__(self):
        super().__init__()
        self.pos_encoding = PositionalEncoding(1000, 512)
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=512, nhead=8, dim_feedforward=1024, batch_first=True
        )
        self.transformer = nn.TransformerEncoder(encoder_layer, num_layers=2)
        self.frame_classifier = nn.Linear(512, 1)
        self.video_classifier = nn.Linear(512, 1)

class FusionModel(nn.Module):
    def __init__(self):
        super().__init__()
        self.fusion_mlp = nn.Sequential(
            nn.Linear(2688, 1024),
            nn.BatchNorm1d(1024),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(1024, 512),
            nn.BatchNorm1d(512),
            nn.ReLU(),
        )

class FullVideoModel(nn.Module):
    def __init__(self):
        super().__init__()
        self.fusion = FusionModel()
        self.temporal = TemporalModel()

    def forward(self, rgb, vit, freq):
        feat = torch.cat([rgb, vit, freq], dim=-1)
        b, t, d = feat.shape
        feat_flat = feat.view(b * t, d)
        fused_flat = self.fusion.fusion_mlp(feat_flat)
        fused = fused_flat.view(b, t, -1)
        pos = self.temporal.pos_encoding(fused)
        trans = self.temporal.transformer(pos)
        frame_logits = self.temporal.frame_classifier(trans).squeeze(-1)
        video_logits = self.temporal.video_classifier(trans.mean(dim=1))
        return {"frame_logits": frame_logits, "video_logits": video_logits}


def compute_roc_auc(y_true, y_scores):
    """Simple Mann-Whitney U / rank-sum ROC-AUC computation in pure Python."""
    pos = [s for y, s in zip(y_true, y_scores) if y == 1]
    neg = [s for y, s in zip(y_true, y_scores) if y == 0]
    if not pos or not neg:
        return 0.5
    count = 0.0
    for p in pos:
        for n in neg:
            if p > n:
                count += 1.0
            elif p == n:
                count += 0.5
    return count / (len(pos) * len(neg))


def run_evaluation(num_samples_per_category=200):
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Running evaluation on device: {device}")

    # Load Model & Scaler
    model = FullVideoModel().to(device)
    model.load_state_dict(torch.load("data/models/video_fusion_best.pt", map_location=device))
    model.eval()

    scaler_ckpt = torch.load("data/models/video_scaler.pt", map_location=device)
    temperature = scaler_ckpt["temperature"].item()
    print(f"Loaded calibration temperature: {temperature:.4f}")

    categories = [
        ("original", 0),
        ("Face2Face", 1),
        ("FaceSwap", 1),
        ("FaceShifter", 1),
        ("NeuralTextures", 1),
        ("Deepfakes", 1),
        ("DeepFakeDetection", 1),
    ]

    y_true_all = []
    y_pred_probs = []
    y_pred_labels = []
    category_results = {}

    start_time = time.perf_counter()

    with torch.no_grad():
        for cat_name, true_label in categories:
            cat_dir = os.path.join("data/embeddings", cat_name)
            if not os.path.exists(cat_dir):
                continue

            files = os.listdir(cat_dir)[:num_samples_per_category]
            cat_probs = []
            cat_preds = []

            for f in files:
                file_path = os.path.join(cat_dir, f)
                data = torch.load(file_path, map_location=device)

                rgb = data["rgb"].unsqueeze(0).to(device)
                vit = data["vit"].unsqueeze(0).to(device)
                freq = data["freq"].unsqueeze(0).to(device)

                out = model(rgb, vit, freq)
                logit = out["video_logits"]
                calibrated_logit = logit / temperature
                prob = torch.sigmoid(calibrated_logit).item()
                pred = 1 if prob >= 0.5 else 0

                cat_probs.append(prob)
                cat_preds.append(pred)
                y_true_all.append(true_label)
                y_pred_probs.append(prob)
                y_pred_labels.append(pred)

            correct = sum(1 for p in cat_preds if p == true_label)
            cat_acc = correct / len(cat_preds) if cat_preds else 0.0
            category_results[cat_name] = {
                "accuracy": round(float(cat_acc), 4),
                "samples": len(cat_preds),
                "mean_score": round(float(sum(cat_probs) / len(cat_probs)), 4) if cat_probs else 0.0,
            }

    elapsed_sec = time.perf_counter() - start_time

    # Confusion matrix: TP, TN, FP, FN
    tp = sum(1 for yt, yp in zip(y_true_all, y_pred_labels) if yt == 1 and yp == 1)
    tn = sum(1 for yt, yp in zip(y_true_all, y_pred_labels) if yt == 0 and yp == 0)
    fp = sum(1 for yt, yp in zip(y_true_all, y_pred_labels) if yt == 0 and yp == 1)
    fn = sum(1 for yt, yp in zip(y_true_all, y_pred_labels) if yt == 1 and yp == 0)

    total = len(y_true_all)
    acc = (tp + tn) / total if total > 0 else 0.0
    prec = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    rec = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = 2 * prec * rec / (prec + rec) if (prec + rec) > 0 else 0.0
    auc = compute_roc_auc(y_true_all, y_pred_probs)

    print("\n" + "=" * 55)
    print("        MODEL BENCHMARK EVALUATION RESULTS")
    print("=" * 55)
    print(f"Total Samples Evaluated: {total}")
    print(f"Total Evaluation Time:   {elapsed_sec:.2f}s ({total/elapsed_sec:.1f} FPS)")
    print(f"Overall Accuracy:        {acc * 100:.2f}%")
    print(f"ROC-AUC Score:           {auc:.4f}")
    print(f"Precision:               {prec * 100:.2f}%")
    print(f"Recall:                  {rec * 100:.2f}%")
    print(f"F1-Score:                {f1:.4f}")
    print("\nConfusion Matrix:")
    print(f"  • True Negatives (Authentic Correct):  {tn} / {tn + fp}")
    print(f"  • False Positives (Authentic as Fake): {fp} / {tn + fp}")
    print(f"  • False Negatives (Fake as Authentic): {fn} / {tp + fn}")
    print(f"  • True Positives (Fake Correct):       {tp} / {tp + fn}")

    print("\nPer-Category Detection Rates:")
    for cat, m in category_results.items():
        type_str = "AUTHENTIC" if cat == "original" else "MANIPULATED"
        print(f"  • {cat:<18} [{type_str}]: {m['accuracy']*100:.1f}% (Mean Fake Prob: {m['mean_score']:.3f}, N={m['samples']})")
    print("=" * 55)


if __name__ == "__main__":
    run_evaluation(num_samples_per_category=150)
