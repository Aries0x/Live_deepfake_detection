"""
Pure NumPy / PyTorch Metric Computation Utilities.
Calculates Accuracy, Precision, Recall, F1, ROC-AUC (Mann-Whitney U),
Brier Score, and Confusion Matrix without external C-extensions.
"""
from typing import Dict, Any, List, Union
import numpy as np


def compute_binary_metrics(
    targets: Union[List[int], np.ndarray],
    probs: Union[List[float], np.ndarray],
    threshold: float = 0.5,
) -> Dict[str, Any]:
    targets = np.array(targets, dtype=int)
    probs = np.array(probs, dtype=float)
    preds = (probs >= threshold).astype(int)

    tp = int(np.sum((preds == 1) & (targets == 1)))
    tn = int(np.sum((preds == 0) & (targets == 0)))
    fp = int(np.sum((preds == 1) & (targets == 0)))
    fn = int(np.sum((preds == 0) & (targets == 1)))

    total = max(1, len(targets))
    acc = float(tp + tn) / total
    prec = float(tp) / max(1e-7, tp + fp)
    rec = float(tp) / max(1e-7, tp + fn)
    f1 = 2.0 * prec * rec / max(1e-7, prec + rec)
    brier = float(np.mean((probs - targets) ** 2))

    # Mann-Whitney U test for exact ROC-AUC calculation
    n_pos = int(np.sum(targets == 1))
    n_neg = int(np.sum(targets == 0))
    if n_pos == 0 or n_neg == 0:
        auc = 0.5
    else:
        order = np.argsort(probs)
        ranks = np.empty_like(order)
        ranks[order] = np.arange(len(probs)) + 1
        rank_sum_pos = np.sum(ranks[targets == 1])
        u_pos = rank_sum_pos - (n_pos * (n_pos + 1)) / 2.0
        auc = float(u_pos / (n_pos * n_neg))

    return {
        "accuracy": round(acc, 4),
        "precision": round(prec, 4),
        "recall": round(rec, 4),
        "f1": round(f1, 4),
        "roc_auc": round(auc, 4),
        "brier_score": round(brier, 4),
        "confusion_matrix": [[tn, fp], [fn, tp]],
        "tp": tp,
        "tn": tn,
        "fp": fp,
        "fn": fn,
    }
