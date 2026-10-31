#!/usr/bin/env python3
"""Export a trained YOLOv7-tiny checkpoint to ONNX as in the paper."""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
YOLO = ROOT / "vendor/yolov7"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--task", choices=["bee", "pollen"], required=True)
    parser.add_argument("--epochs", type=int, default=100)
    args = parser.parse_args()
    weights = ROOT / f"runs/train/{args.task}_yolov7_tiny_e{args.epochs}/weights/best.pt"
    subprocess.run(
        [sys.executable, str(YOLO / "export.py"), "--weights", str(weights), "--img-size", "416", "416", "--grid"],
        cwd=YOLO,
        check=True,
    )


if __name__ == "__main__":
    main()

