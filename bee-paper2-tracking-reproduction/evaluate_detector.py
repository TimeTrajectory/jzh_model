"""Evaluate the trained detector on the untouched BEE22 test sequences."""
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
    parser.add_argument("--weights", type=Path, default=ROOT / "runs/detector/yolov5s_seed50/weights/best.pt")
    parser.add_argument("--batch", type=int, default=32)
    parser.add_argument("--device", default="auto")
    args = parser.parse_args()
    device = "0" if args.device == "auto" and torch.cuda.is_available() else (
        "cpu" if args.device == "auto" else args.device
    )
    required = [ROOT / "vendor/yolov5/val.py", ROOT / "bee22_test.yaml", args.weights]
    missing = [str(path) for path in required if not path.is_file()]
    if missing:
        parser.error("missing prerequisites: " + ", ".join(missing))
    command = [
        sys.executable, str(ROOT / "vendor/yolov5/val.py"),
        "--weights", str(args.weights), "--data", str(ROOT / "bee22_test.yaml"),
        "--imgsz", "640", "--batch-size", str(args.batch), "--device", device,
        "--workers", "4", "--project", str(ROOT / "runs/evaluation"),
        "--name", "detector_test", "--exist-ok", "--task", "val",
    ]
    environment = os.environ.copy()
    environment["LD_LIBRARY_PATH"] = str(Path(sys.base_prefix) / "lib") + ":" + environment.get("LD_LIBRARY_PATH", "")
    subprocess.run(command, cwd=ROOT, env=environment, check=True)


if __name__ == "__main__":
    main()
