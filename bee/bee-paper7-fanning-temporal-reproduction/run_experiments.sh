#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"; cd "$ROOT"
for encoding in rgb tsg tem; do
  run_dir="runs/train/fast_yolo11n_${encoding}"
  .venv/bin/python train.py "$encoding" --model weights/yolo11n.pt --epochs 50 --batch 32 --workers 8 --patience 15 --name "fast_yolo11n_${encoding}"
  .venv/bin/python evaluate.py "$encoding" --weights "$run_dir/weights/best.pt" --batch 32 --workers 0
done
.venv/bin/python update_results.py
.venv/bin/python generate_documents.py
