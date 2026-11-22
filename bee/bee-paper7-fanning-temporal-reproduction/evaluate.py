#!/usr/bin/env python3
"""Evaluate one trained arm and save machine-readable metrics."""
from pathlib import Path
import argparse
import json
import time
import yaml
from ultralytics import YOLO
from temporal_loader import install

ROOT = Path(__file__).resolve().parent

def main():
    p = argparse.ArgumentParser()
    p.add_argument("encoding", choices=("rgb", "tsg", "tem"))
    p.add_argument("--weights", type=Path)
    p.add_argument("--batch", type=int, default=32)
    p.add_argument("--workers", type=int, default=0,
                   help="Evaluation workers; zero avoids dataloader hangs with temporal decoding.")
    p.add_argument("--device", default="0")
    a = p.parse_args()
    weights = a.weights or ROOT / f"runs/train/fast_yolo11n_{a.encoding}/weights/best.pt"
    install(a.encoding)
    model = YOLO(str(weights))
    start = time.time()
    dataset = yaml.safe_load((ROOT / f"dataset_{a.encoding}.yaml").read_text())
    dataset["path"] = str(ROOT / f"data/{a.encoding}")
    m = model.val(data=dataset, imgsz=1024, rect=True,
                  batch=a.batch, workers=a.workers, device=a.device, plots=True,
                  project=str(ROOT / "runs/eval"), name=f"fast_yolo11n_{a.encoding}")
    result = {"encoding": a.encoding, "weights": str(weights),
              "precision": float(m.box.mp), "recall": float(m.box.mr),
              "map50": float(m.box.map50), "map50_95": float(m.box.map),
              "elapsed_seconds": time.time() - start, "speed_ms": m.speed,
              "evaluation_workers": a.workers}
    out = ROOT / "results"
    out.mkdir(exist_ok=True)
    (out / f"metrics_yolo11n_{a.encoding}.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()
