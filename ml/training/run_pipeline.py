"""
End-to-End Multimodal Training Pipeline Runner.
Orchestrates:
  0. Scaled Multimodal Extraction (Face crops + 16kHz speech audio)
  1. Train EfficientNet-B0 with staged layer unfreezing on extracted face crops
  2. Train ViT-B/16 with top-layer self-attention tuning on extracted face crops
  3. Train AASIST-L on extracted speech audio spectrograms
  4. Train Temporal GRU on sequence trajectories
  5. Run Comprehensive Evaluation & Save Benchmark Metrics
"""
import os
import sys
import time
import json

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from ml.training.extract_multimodal import extract_video_face_crops, generate_audio_dataset
from ml.training.train_visual import run_visual_finetuning
from ml.training.train_audio import train_audio_model
from ml.training.train_temporal import train_temporal_model
from ml.training.evaluate_all import evaluate_all


def run_full_training_pipeline():
    start_total = time.perf_counter()
    print("======================================================================")
    print("   STARTING END-TO-END MULTIMODAL MEDIA INTEGRITY MODEL TRAINING      ")
    print("======================================================================")

    # Step 0: Extract Scaled Multimodal Data
    print("\n[PHASE 0/4] Extracting & Preprocessing Multimodal Dataset (Face Crops + Audio)...")
    extract_video_face_crops()
    generate_audio_dataset()

    # Step 1: Visual Models (EfficientNet-B0 + ViT-B/16)
    print("\n[PHASE 1/4] Training Visual Models (EfficientNet-B0 + ViT-B/16)...")
    visual_results = run_visual_finetuning(epochs=4)

    # Step 2: Audio Model (AASIST-L)
    print("\n[PHASE 2/4] Training Audio Anti-Spoofing Model (AASIST-L)...")
    audio_results = train_audio_model(epochs=5, batch_size=16)

    # Step 3: Temporal Sequence Model (Temporal GRU)
    print("\n[PHASE 3/4] Training Temporal GRU Sequence Model...")
    temporal_results = train_temporal_model(epochs=6, batch_size=16)

    # Step 4: Comprehensive Benchmark & Evaluation
    print("\n[PHASE 4/4] Running Benchmark Evaluation on Held-Out Test Partitions...")
    benchmark_metrics = evaluate_all()

    total_time_min = (time.perf_counter() - start_total) / 60.0
    print("\n======================================================================")
    print(f"   MULTIMODAL TRAINING COMPLETE IN {total_time_min:.2f} MINUTES        ")
    print("======================================================================")
    return {
        "visual": visual_results,
        "audio": audio_results,
        "temporal": temporal_results,
        "benchmark": benchmark_metrics,
        "duration_minutes": round(total_time_min, 2),
    }


if __name__ == "__main__":
    run_full_training_pipeline()
