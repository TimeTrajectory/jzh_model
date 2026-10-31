#!/usr/bin/env python3
"""Run paper-aligned YOLOv7-tiny training experiments."""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
YOLO = ROOT / "vendor/yolov7"


def train(task: str, epochs: int, batch: int, device: str, workers: int, resume: bool) -> None:
    name = f"{task}_yolov7_tiny_e{epochs}"
    last = ROOT / f"runs/train/{name}/weights/last.pt"
    command = [sys.executable, str(YOLO / "train.py")]
    if resume and last.exists():
        command += ["--resume", str(last)]
    else:
        command += [
            "--workers", str(workers),
            "--device", device,
            "--batch-size", str(batch),
            "--data", str(ROOT / f"data/{task}.yaml"),
            "--img-size", "416", "416",
            "--cfg", str(YOLO / "cfg/training/yolov7-tiny.yaml"),
            "--weights", str(ROOT / "weights/yolov7-tiny.pt"),
            "--hyp", str(YOLO / "data/hyp.scratch.tiny.yaml"),
            "--epochs", str(epochs),
            "--project", str(ROOT / "runs/train"),
            "--name", name,
            "--exist-ok",
        ]
    print("+", " ".join(command), flush=True)
    subprocess.run(command, cwd=YOLO, check=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--task", choices=["bee", "pollen", "all"], default="all")
    parser.add_argument("--epochs", type=int, default=100)
    parser.add_argument("--batch", type=int, default=8)
    parser.add_argument("--device", default="0")
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()
    tasks = ["bee", "pollen"] if args.task == "all" else [args.task]
    for task in tasks:
        train(task, args.epochs, args.batch, args.device, args.workers, args.resume)


if __name__ == "__main__":
    main()

