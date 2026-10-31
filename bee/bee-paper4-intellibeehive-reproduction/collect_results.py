#!/usr/bin/env python3
"""Collect compact, reviewable artifacts from completed YOLOv7 runs."""
from __future__ import annotations

import csv
import json
import platform
import re
import shutil
from pathlib import Path

import torch

ROOT = Path(__file__).resolve().parent
COLUMNS = [
    "epoch", "gpu_mem", "train_box", "train_obj", "train_cls", "train_total",
    "labels", "img_size", "precision", "recall", "map50", "map50_95",
    "val_box", "val_obj", "val_cls",
]


def parse_history(task: str) -> list[dict]:
    source = ROOT / f"runs/train/{task}_yolov7_tiny_e100/results.txt"
    rows = []
    for epoch, line in enumerate(source.read_text().splitlines()):
        values = line.split()
        row = dict(zip(COLUMNS, values))
        row["epoch"] = epoch
        for key in COLUMNS[2:]:
            if key in row:
                row[key] = float(row[key])
        row["fitness"] = 0.1 * row["map50"] + 0.9 * row["map50_95"]
        rows.append(row)
    output = ROOT / f"results/{task}_training_history.csv"
    with output.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    return rows


def parse_test_log(task: str) -> list[dict]:
    log = (ROOT / f"results/{task}_evaluation_log.txt").read_text(errors="ignore")
    pattern = re.compile(
        r"^\s*(all|ordinary_bee|pollen_bearing_bee)\s+(\d+)\s+(\d+)\s+"
        r"([0-9.]+)\s+([0-9.]+)\s+([0-9.]+)\s+([0-9.]+)\s*$", re.MULTILINE
    )
    rows = []
    for match in pattern.finditer(log):
        name, images, labels, precision, recall, map50, map50_95 = match.groups()
        p, r = float(precision), float(recall)
        rows.append({
            "class": name,
            "images": int(images),
            "labels": int(labels),
            "precision": p,
            "recall": r,
            "f1": 2 * p * r / (p + r) if p + r else 0.0,
            "map50": float(map50),
            "map50_95": float(map50_95),
        })
    speed = re.search(r"Speed:\s*([0-9.]+)/([0-9.]+)/([0-9.]+) ms", log)
    return rows, ({"inference_ms": float(speed.group(1)), "nms_ms": float(speed.group(2)), "total_ms": float(speed.group(3))} if speed else {})


def copy_figures(task: str) -> list[str]:
    output = ROOT / "results/figures"
    output.mkdir(parents=True, exist_ok=True)
    copied = []
    sources = {
        "training_results.png": ROOT / f"runs/train/{task}_yolov7_tiny_e100/results.png",
        "test_pr_curve.png": ROOT / f"runs/eval/{task}_yolov7_tiny_e100_test/PR_curve.png",
        "test_f1_curve.png": ROOT / f"runs/eval/{task}_yolov7_tiny_e100_test/F1_curve.png",
        "test_confusion_matrix.png": ROOT / f"runs/eval/{task}_yolov7_tiny_e100_test/confusion_matrix.png",
        "test_predictions.jpg": ROOT / f"runs/eval/{task}_yolov7_tiny_e100_test/test_batch0_pred.jpg",
    }
    for label, source in sources.items():
        destination = output / f"{task}_{label}"
        shutil.copy2(source, destination)
        copied.append(str(destination.relative_to(ROOT)))
    return copied


def main() -> None:
    (ROOT / "results").mkdir(exist_ok=True)
    dataset = json.loads((ROOT / "data/dataset_summary.json").read_text())
    experiments = {}
    for task in ("bee", "pollen"):
        history = parse_history(task)
        best = max(history, key=lambda row: row["fitness"])
        test_rows, speed = parse_test_log(task)
        experiments[task] = {
            "protocol": {"architecture": "YOLOv7-tiny", "epochs": 100, "image_size": 416, "batch_size": 8},
            "best_validation_epoch_zero_based": best["epoch"],
            "best_validation": {key: best[key] for key in ("precision", "recall", "map50", "map50_95", "fitness")},
            "independent_test": test_rows,
            "speed_rtx4090_batch8": speed,
            "figures": copy_figures(task),
        }
    summary = {
        "generated_date": "2026-10-31",
        "paper": "IntelliBeeHive: An Automated Honey Bee, Pollen, and Varroa Destructor Monitoring System",
        "reproduction_scope": "public-data substitute; original author data/code unavailable",
        "dataset": dataset,
        "experiments": experiments,
        "tracking": json.loads((ROOT / "results/tracking_evaluation.json").read_text()),
        "environment": {
            "python": platform.python_version(),
            "platform": platform.platform(),
            "torch": torch.__version__,
            "cuda_available": torch.cuda.is_available(),
            "gpu": torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
        },
    }
    (ROOT / "results/metrics_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

