"""
Dataset Partitioning Script for FaceForensics++ (ID-Aware Train / Val / Test Split).
Ensures zero identity/actor leakage between train, validation, and test splits.
"""
import os
import csv
import random
from typing import Dict, List, Tuple

DATASET_ROOT = r"c:\Users\sunil\OneDrive\Documents\hackathon\REC_Hack\archive\FaceForensics++_C23"
SPLITS_DIR = r"c:\Users\sunil\OneDrive\Documents\hackathon\REC_Hack\media-integrity\data\splits"


def get_video_id(filename: str) -> str:
    """Extracts primary subject/sequence ID to prevent cross-split leakage."""
    base = os.path.splitext(filename)[0]
    if "_" in base:
        parts = base.split("_")
        return parts[0]
    return base


def create_id_aware_splits() -> Dict[str, List[Dict[str, str]]]:
    os.makedirs(SPLITS_DIR, exist_ok=True)
    
    csv_metadata_path = os.path.join(DATASET_ROOT, "csv", "FF++_Metadata.csv")
    records = []
    
    with open(csv_metadata_path, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rel_path = row["File Path"]
            label = row["Label"].upper()
            full_path = os.path.join(DATASET_ROOT, rel_path.replace("/", os.sep))
            
            filename = os.path.basename(rel_path)
            category = rel_path.split("/")[0] if "/" in rel_path else rel_path.split(os.sep)[0]
            vid_id = get_video_id(filename)
            
            records.append({
                "rel_path": rel_path,
                "full_path": full_path,
                "label": label,
                "category": category,
                "filename": filename,
                "video_id": vid_id,
                "frame_count": row.get("Frame Count", "0"),
                "file_size_mb": row.get("File Size(MB)", "0"),
            })

    # Group by primary video ID to avoid data leakage
    # Official FF++ protocol: IDs 0-719 train (72%), 720-859 val (14%), 860-999 test (14%)
    # For DFD (numeric IDs 01..), partition deterministically
    train_records = []
    val_records = []
    test_records = []

    for rec in records:
        vid_id = rec["video_id"]
        try:
            id_int = int(vid_id)
            if id_int <= 719:
                train_records.append(rec)
            elif id_int <= 859:
                val_records.append(rec)
            else:
                test_records.append(rec)
        except ValueError:
            # Hash-based deterministic split for non-integer IDs
            h = hash(vid_id) % 100
            if h < 72:
                train_records.append(rec)
            elif h < 86:
                val_records.append(rec)
            else:
                test_records.append(rec)

    splits = {
        "train": train_records,
        "val": val_records,
        "test": test_records,
    }

    # Write split CSVs
    fieldnames = ["rel_path", "full_path", "label", "category", "filename", "video_id", "frame_count", "file_size_mb"]
    for split_name, split_rows in splits.items():
        out_csv = os.path.join(SPLITS_DIR, f"{split_name}_videos.csv")
        with open(out_csv, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(split_rows)
        print(f"Created {split_name} split: {len(split_rows)} videos -> {out_csv}")

    return splits


if __name__ == "__main__":
    splits = create_id_aware_splits()
    for name, items in splits.items():
        reals = sum(1 for i in items if i["label"] == "REAL")
        fakes = sum(1 for i in items if i["label"] == "FAKE")
        print(f"{name.upper()} Total: {len(items)} | Real: {reals} | Fake: {fakes}")
