#!/usr/bin/env python3
"""Run either trained detector on images, folders, or video."""
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
    parser.add_argument("--source", required=True)
    parser.add_argument("--epochs", type=int, default=100)
    parser.add_argument("--confidence", type=float, default=0.25)
    parser.add_argument("--device", default="0")
    args = parser.parse_args()
    weights = ROOT / f"runs/train/{args.task}_yolov7_tiny_e{args.epochs}/weights/best.pt"
    command = [
        sys.executable, str(YOLO / "detect.py"),
        "--weights", str(weights),
        "--source", args.source,
        "--img-size", "416",
        "--conf-thres", str(args.confidence),
        "--device", args.device,
        "--project", str(ROOT / "runs/predict"),
        "--name", args.task,
        "--exist-ok",
        "--save-txt", "--save-conf",
    ]
    subprocess.run(command, cwd=YOLO, check=True)


if __name__ == "__main__":
    main()

