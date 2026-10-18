"""Train the paper's YOLOv10X baseline with documented parameters."""
from __future__ import annotations

import argparse
from pathlib import Path

from ultralytics import YOLO


ROOT = Path(__file__).resolve().parent


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="weights/yolov10x.pt")
    parser.add_argument("--data", type=Path, default=ROOT / "dataset.yaml")
    parser.add_argument("--epochs", type=int, default=100, help="Early stopping normally ends near the paper's 45 epochs")
    parser.add_argument("--batch", type=int, default=4)
    parser.add_argument("--imgsz", type=int, default=1080)
    parser.add_argument("--device", default="0")
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--seed", type=int, default=50)
    parser.add_argument("--name", default="yolov10x_seed50")
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()

    model_source = ROOT / "runs/detector" / args.name / "weights/last.pt" if args.resume else args.model
    model = YOLO(str(model_source))
    if args.resume:
        model.train(resume=True)
        return
    model.train(
        data=str(args.data),
        epochs=args.epochs,
        patience=10,
        batch=args.batch,
        imgsz=args.imgsz,
        optimizer="SGD",
        lr0=0.01,
        lrf=0.01,
        cos_lr=False,
        fliplr=0.4,
        degrees=10.0,
        seed=args.seed,
        deterministic=True,
        device=args.device,
        workers=args.workers,
        project=str(ROOT / "runs/detector"),
        name=args.name,
        exist_ok=True,
        plots=True,
        save=True,
        verbose=True,
    )


if __name__ == "__main__":
    main()

