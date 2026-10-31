#!/usr/bin/env python3
"""Evaluate trained checkpoints on the untouched group-split test set."""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
YOLO = ROOT / "vendor/yolov7"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--task", choices=["bee", "pollen"], required=True)
    parser.add_argument("--epochs", type=int, default=100)
    parser.add_argument("--batch", type=int, default=8)
    parser.add_argument("--device", default="0")
    args = parser.parse_args()
    name = f"{args.task}_yolov7_tiny_e{args.epochs}"
    weights = ROOT / f"runs/train/{name}/weights/best.pt"
    if not weights.exists():
        raise FileNotFoundError(weights)
    output = ROOT / f"runs/eval/{name}_test"
    command = [
        sys.executable, str(YOLO / "test.py"),
        "--data", str(ROOT / f"data/{args.task}_test.yaml"),
        "--img-size", "416",
        "--batch-size", str(args.batch),
        "--conf-thres", "0.001",
        "--iou-thres", "0.65",
        "--device", args.device,
        "--weights", str(weights),
        "--project", str(ROOT / "runs/eval"),
        "--name", f"{name}_test",
        "--exist-ok",
        "--verbose",
    ]
    print("+", " ".join(command), flush=True)
    completed = subprocess.run(command, cwd=YOLO, text=True, capture_output=True)
    print(completed.stdout)
    if completed.stderr:
        print(completed.stderr, file=sys.stderr)
    completed.check_returncode()
    (ROOT / "results").mkdir(exist_ok=True)
    (ROOT / f"results/{args.task}_evaluation_log.txt").write_text(
        completed.stdout + "\n" + completed.stderr, encoding="utf-8"
    )
    print(json.dumps({"task": args.task, "weights": str(weights), "output": str(output)}, indent=2))


if __name__ == "__main__":
    main()

