"""Run inference and report counts for the three bee classes."""
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

from ultralytics import YOLO


ROOT = Path(__file__).resolve().parent


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source")
    parser.add_argument("--weights", default=str(ROOT / "runs/detector/yolov10x_seed50/weights/best.pt"))
    parser.add_argument("--conf", type=float, default=0.25)
    parser.add_argument("--imgsz", type=int, default=1080)
    args = parser.parse_args()

    model = YOLO(args.weights)
    counts: Counter[str] = Counter()
    for result in model.predict(
        source=args.source, conf=args.conf, imgsz=args.imgsz, save=True,
        project=str(ROOT / "runs/predict"), name="demo", exist_ok=True, stream=True,
    ):
        if result.boxes is not None:
            counts.update(result.names[int(value)] for value in result.boxes.cls.tolist())
    print(json.dumps(dict(counts), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

