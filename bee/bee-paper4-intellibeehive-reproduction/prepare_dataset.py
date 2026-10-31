#!/usr/bin/env python3
"""Convert Caltech Honeybee JSON boxes into two group-split YOLO datasets.

Outputs:
  data/caltech_bee     all boxes collapsed to one ``bee`` class
  data/caltech_pollen  ``ordinary_bee`` and ``pollen_bearing_bee`` classes

Images are hard-linked when the filesystem supports it, so the two views do not
duplicate the large source images. Splitting happens by encoded video group
(frame_number // 10000), preventing adjacent frames from crossing splits.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import random
import shutil
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "downloads/Caltech-Honeybee/dataset/pollen_classification"
PARTS = ("random_selection", "pollen_selection")
SPLITS = ("train", "val", "test")


def stable_group_split(groups: list[int], seed: int) -> dict[int, str]:
    """Return a deterministic 70/15/15 split over whole video groups."""
    ordered = sorted(groups)
    random.Random(seed).shuffle(ordered)
    n = len(ordered)
    n_train = round(n * 0.70)
    n_val = round(n * 0.15)
    return {
        group: ("train" if i < n_train else "val" if i < n_train + n_val else "test")
        for i, group in enumerate(ordered)
    }


def link_or_copy(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        return
    try:
        os.link(source, destination)
    except OSError:
        shutil.copy2(source, destination)


def yolo_line(class_id: int, box: list[float], width: int, height: int) -> str:
    x1, y1, x2, y2 = box
    x1, x2 = sorted((max(0.0, x1), min(float(width), x2)))
    y1, y2 = sorted((max(0.0, y1), min(float(height), y2)))
    bw, bh = x2 - x1, y2 - y1
    if bw <= 1 or bh <= 1:
        raise ValueError(f"Degenerate box: {box}")
    xc, yc = x1 + bw / 2, y1 + bh / 2
    return f"{class_id} {xc/width:.8f} {yc/height:.8f} {bw/width:.8f} {bh/height:.8f}"


def write_yaml(path: Path, dataset_path: Path, names: list[str], val_split: str = "val") -> None:
    # The pinned 2022 YOLOv7 parser predates Ultralytics' newer ``path:`` key,
    # so use explicit absolute paths for compatibility.
    text = (
        f"train: {(dataset_path / 'images/train').resolve()}\n"
        f"val: {(dataset_path / f'images/{val_split}').resolve()}\n"
        f"test: {(dataset_path / 'images/test').resolve()}\n"
        f"nc: {len(names)}\n"
        f"names: {names!r}\n"
    )
    path.write_text(text, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=2309)
    parser.add_argument("--clean", action="store_true")
    args = parser.parse_args()
    if not SOURCE.exists():
        raise FileNotFoundError("Caltech data missing. Run: python download_assets.py")

    records = []
    for part in PARTS:
        for label_path in sorted((SOURCE / part / "labels").glob("*.json")):
            payload = json.loads(label_path.read_text(encoding="utf-8"))
            frame = int(label_path.stem)
            image_path = SOURCE / part / "images" / payload["image"]["filename"]
            # The numeric prefix encodes the source-video block in this dataset.
            records.append((part, frame, frame // 10000, image_path, payload))

    split_for_group = stable_group_split(sorted({record[2] for record in records}), args.seed)
    outputs = {
        "bee": (ROOT / "data/caltech_bee", ["bee"]),
        "pollen": (ROOT / "data/caltech_pollen", ["ordinary_bee", "pollen_bearing_bee"]),
    }
    if args.clean:
        for output, _ in outputs.values():
            shutil.rmtree(output, ignore_errors=True)

    stats: dict[str, Counter] = {name: Counter() for name in outputs}
    manifest_rows = []
    for part, frame, group, image_path, payload in records:
        split = split_for_group[group]
        unique_name = f"{part}_{image_path.name}"
        width, height = int(payload["image"]["width"]), int(payload["image"]["height"])
        annotations = payload.get("annotations", [])
        for task, (output, _) in outputs.items():
            target_image = output / "images" / split / unique_name
            target_label = output / "labels" / split / f"{Path(unique_name).stem}.txt"
            link_or_copy(image_path, target_image)
            target_label.parent.mkdir(parents=True, exist_ok=True)
            lines = []
            for annotation in annotations:
                source_class = int(annotation["class_id"])
                target_class = 0 if task == "bee" else source_class
                try:
                    lines.append(yolo_line(target_class, annotation["bbox"], width, height))
                except ValueError:
                    stats[task][f"{split}_dropped_boxes"] += 1
                    continue
                stats[task][f"{split}_class_{target_class}"] += 1
            target_label.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")
            stats[task][f"{split}_images"] += 1
        manifest_rows.append(
            {
                "part": part,
                "frame": frame,
                "video_group": group,
                "split": split,
                "image": unique_name,
                "ordinary_bees": sum(int(a["class_id"]) == 0 for a in annotations),
                "pollen_bearing_bees": sum(int(a["class_id"]) == 1 for a in annotations),
            }
        )

    for task, (output, names) in outputs.items():
        write_yaml(ROOT / f"data/{task}.yaml", output, names)
        write_yaml(ROOT / f"data/{task}_test.yaml", output, names, val_split="test")

    manifest_path = ROOT / "data/split_manifest.csv"
    with manifest_path.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(manifest_rows[0]))
        writer.writeheader()
        writer.writerows(manifest_rows)
    summary = {
        "source": "yibingwei-1/Caltech-Honeybee",
        "source_commit": "0a06fabcf23bbc75f03af4b028f8070bda8a2649",
        "split_seed": args.seed,
        "group_rule": "integer frame id // 10000; same group never crosses splits",
        "group_counts": dict(Counter(split_for_group.values())),
        "tasks": {task: dict(counter) for task, counter in stats.items()},
        "manifest_sha256": hashlib.sha256(manifest_path.read_bytes()).hexdigest(),
    }
    (ROOT / "data/dataset_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

