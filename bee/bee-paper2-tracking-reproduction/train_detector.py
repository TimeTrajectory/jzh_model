"""Launch the fixed YOLOv5s detector experiment used in this reproduction."""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

import torch

ROOT = Path(__file__).resolve().parent


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--epochs", type=int, default=14)
    parser.add_argument("--batch", type=int, default=32)
    parser.add_argument("--seed", type=int, default=50)
    parser.add_argument("--device", default="auto")
    parser.add_argument("--name", default="yolov5s_seed50")
    args = parser.parse_args()
    device = "0" if args.device == "auto" and torch.cuda.is_available() else (
        "cpu" if args.device == "auto" else args.device
    )
    required = [ROOT / "vendor/yolov5/train.py", ROOT / "weights/yolov5s-v7.0.pt", ROOT / "bee22.yaml"]
    missing = [str(path) for path in required if not path.is_file()]
    if missing:
        parser.error("missing prerequisites: " + ", ".join(missing))
    command = [
        sys.executable, str(ROOT / "vendor/yolov5/train.py"),
        "--weights", str(ROOT / "weights/yolov5s-v7.0.pt"),
        "--data", str(ROOT / "bee22.yaml"),
        "--hyp", str(ROOT / "hyp.bee22.yaml"),
        "--imgsz", "640", "--batch-size", str(args.batch),
        "--epochs", str(args.epochs), "--optimizer", "Adam",
        "--seed", str(args.seed), "--workers", "4", "--device", device,
        "--project", str(ROOT / "runs/detector"), "--name", args.name,
    ]
    environment = os.environ.copy()
    environment["LD_LIBRARY_PATH"] = str(Path(sys.base_prefix) / "lib") + ":" + environment.get("LD_LIBRARY_PATH", "")
    subprocess.run(command, cwd=ROOT, env=environment, check=True)


if __name__ == "__main__":
    main()
