#!/usr/bin/env python3
"""Prepare BEE22 as a sequence-disjoint Darknet dataset for paper P05."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DEFAULT_SOURCE = ROOT.parent / "bee-paper2-tracking-reproduction" / "data" / "yolo"
SPLITS = ("train", "val", "test")


def link(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists() or dst.is_symlink():
        return
    try:
        os.link(src.resolve(), dst)
    except OSError:
        dst.symlink_to(src.resolve())


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    args = ap.parse_args()
    source = args.source.resolve()
    if not source.exists():
        raise SystemExit(f"BEE22 YOLO source not found: {source}\nRun download/prepare in paper 2 first.")

    out = ROOT / "data" / "bee22_darknet"
    rows, summary = [], {"source": str(source), "splits": {}}
    for split in SPLITS:
        images = sorted((source / "images" / split).rglob("*.jpg"))
        boxes = 0
        sequences = set()
        list_lines = []
        for image in images:
            seq = image.parent.name
            sequences.add(seq)
            label = source / "labels" / split / seq / f"{image.stem}.txt"
            rel = Path(split) / seq / image.name
            dst_image = out / "images" / rel
            # This pinned Darknet build resolves labels beside each image.
            dst_label = out / "images" / rel.with_suffix(".txt")
            link(image, dst_image)
            link(label, dst_label)
            n = sum(1 for line in label.read_text().splitlines() if line.strip())
            boxes += n
            list_lines.append(str(dst_image.resolve()))
            rows.append((split, seq, image.name, n))
        (out / f"{split}.txt").write_text("\n".join(list_lines) + "\n")
        summary["splits"][split] = {
            "images": len(images), "boxes": boxes, "sequences": sorted(sequences)
        }

    (out / "bee.names").write_text("bee\n")
    (out / "bee.data").write_text(
        f"classes = 1\ntrain = {out/'train.txt'}\nvalid = {out/'val.txt'}\n"
        f"names = {out/'bee.names'}\nbackup = {ROOT/'runs'/'train'/'backup'}\n"
    )
    (out / "bee_test.data").write_text(
        f"classes = 1\ntrain = {out/'train.txt'}\nvalid = {out/'test.txt'}\n"
        f"names = {out/'bee.names'}\nbackup = {ROOT/'runs'/'train'/'backup'}\n"
    )
    with (ROOT / "data" / "split_manifest.csv").open("w", newline="") as f:
        w = csv.writer(f); w.writerow(("split", "sequence", "image", "boxes")); w.writerows(rows)
    manifest_sha = hashlib.sha256((ROOT / "data" / "split_manifest.csv").read_bytes()).hexdigest()
    summary["manifest_sha256"] = manifest_sha
    summary["split_policy"] = "BEE22 sequences are disjoint; BEE22-15 is validation, 12/13/16 are test."
    (ROOT / "data" / "dataset_summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False)+"\n")
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
