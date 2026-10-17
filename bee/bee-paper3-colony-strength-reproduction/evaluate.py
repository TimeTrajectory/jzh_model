"""Evaluate a trained detector on the fixed test split and save machine-readable metrics."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from ultralytics import YOLO


ROOT = Path(__file__).resolve().parent
NAMES = ["WB no pollen", "WB pollen", "Drone bee"]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--weights", type=Path, default=ROOT / "runs/detector/yolov10x_seed50/weights/best.pt")
    parser.add_argument("--data", type=Path, default=ROOT / "dataset.yaml")
    parser.add_argument("--imgsz", type=int, default=1080)
    parser.add_argument("--batch", type=int, default=4)
    parser.add_argument("--device", default="0")
    args = parser.parse_args()

    model = YOLO(str(args.weights))
    result = model.val(
        data=str(args.data), split="test", imgsz=args.imgsz, batch=args.batch,
        device=args.device, conf=0.001, iou=0.6, plots=True, save_json=True,
        project=str(ROOT / "runs/evaluation"), name="test", exist_ok=True,
    )
    box = result.box
    precision = float(box.mp)
    recall = float(box.mr)
    class_ids = [int(value) for value in box.ap_class_index.tolist()]
    per_class = {
        NAMES[class_id]: {
            "precision": float(box.p[index]),
            "recall": float(box.r[index]),
            "f1": float(box.f1[index]),
            "ap50": float(box.ap50[index]),
            "map50_95": float(box.ap[index]),
        }
        for index, class_id in enumerate(class_ids)
    }
    speed_ms_per_image = {key: float(value) for key, value in result.speed.items()}
    inference_ms = speed_ms_per_image.get("inference", 0.0)
    metrics = {
        "weights": str(args.weights.relative_to(ROOT)),
        "weights_sha256": sha256(args.weights),
        "precision": precision,
        "recall": recall,
        "f1_from_mean_precision_recall": 2 * precision * recall / (precision + recall) if precision + recall else 0.0,
        "map50": float(box.map50),
        "map50_95": float(box.map),
        "per_class": per_class,
        "speed_ms_per_image": speed_ms_per_image,
        "inference_fps": 1000.0 / inference_ms if inference_ms else None,
        "paper_yolov10_accuracy": 0.939,
        "paper_yolov10_f1": 0.92,
        "note": "The paper's custom accuracy is not directly equivalent to Ultralytics mAP metrics.",
    }
    destination = ROOT / "results"
    destination.mkdir(exist_ok=True)
    (destination / "detector_metrics.json").write_text(json.dumps(metrics, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps(metrics, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()

