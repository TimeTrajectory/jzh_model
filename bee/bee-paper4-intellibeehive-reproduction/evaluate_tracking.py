#!/usr/bin/env python3
"""Evaluate the paper's midpoint association rule on public BEE22 MOT labels.

Ground-truth boxes are fed to the tracker so this experiment isolates association
and trigger counting from detector errors. Ground-truth identities are used only
after association to compute track purity and ID-switch diagnostics.
"""
from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path

from PIL import Image

from tracking import Detection, IntelliBeeTracker

ROOT = Path(__file__).resolve().parent
DEFAULT_BEE22 = ROOT.parent / "bee-paper2-tracking-reproduction/data/BEE22"


def read_mot(path: Path) -> dict[int, list[Detection]]:
    frames: dict[int, list[Detection]] = defaultdict(list)
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        parts = line.split(",")
        frame, identity = int(parts[0]), int(parts[1])
        x, y, width, height = map(float, parts[2:6])
        frames[frame].append(Detection(x, y, x + width, y + height, source_id=identity))
    return frames


def ground_truth_crossings(frames: dict[int, list[Detection]], height: int) -> Counter:
    by_identity: dict[int, list[tuple[int, float]]] = defaultdict(list)
    for frame, detections in frames.items():
        for detection in detections:
            by_identity[int(detection.source_id)].append((frame, detection.midpoint[1]))
    upper, lower = height / 3, 2 * height / 3
    counts = Counter()
    for observations in by_identity.values():
        observations.sort()
        for (_, previous), (_, current) in zip(observations, observations[1:]):
            if previous > upper >= current:
                counts["Arriving"] += 1
            elif previous < lower <= current:
                counts["Leaving"] += 1
    return counts


def evaluate_sequence(sequence: Path) -> dict:
    image_path = next((sequence / "img1").glob("*.jpg"))
    width, height = Image.open(image_path).size
    frames = read_mot(sequence / "gt/gt.txt")
    tracker = IntelliBeeTracker(width, height)
    predicted_to_sources: dict[int, list[int]] = defaultdict(list)
    source_last_prediction: dict[int, int] = {}
    id_switches = 0
    assignments = 0
    for frame_index in sorted(frames):
        profiles = tracker.update(frames[frame_index], frame_index)
        for profile in profiles:
            if not profile.source_ids:
                continue
            source = profile.source_ids[-1]
            predicted_to_sources[profile.track_id].append(source)
            if source in source_last_prediction and source_last_prediction[source] != profile.track_id:
                id_switches += 1
            source_last_prediction[source] = profile.track_id
            assignments += 1
    correct = sum(Counter(ids).most_common(1)[0][1] for ids in predicted_to_sources.values() if ids)
    truth = ground_truth_crossings(frames, height)
    count_errors = {
        key: abs(tracker.counts[key] - truth[key]) for key in ("Arriving", "Leaving")
    }
    return {
        "sequence": sequence.name,
        "frames": len(frames),
        "resolution": [width, height],
        "tolerance_px": tracker.tolerance,
        "assignments": assignments,
        "track_purity": correct / assignments if assignments else 0.0,
        "id_switches": id_switches,
        "predicted_crossings": tracker.counts,
        "ground_truth_crossings": dict(truth),
        "absolute_count_error": count_errors,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--bee22-root", type=Path, default=DEFAULT_BEE22)
    parser.add_argument("--split", choices=["train", "test"], default="test")
    parser.add_argument("--sequences", nargs="*")
    args = parser.parse_args()
    split_root = args.bee22_root / args.split
    sequences = sorted(path for path in split_root.iterdir() if path.is_dir())
    if args.sequences:
        allowed = set(args.sequences)
        sequences = [path for path in sequences if path.name in allowed]
    results = [evaluate_sequence(sequence) for sequence in sequences]
    total_assignments = sum(item["assignments"] for item in results)
    weighted_purity = (
        sum(item["track_purity"] * item["assignments"] for item in results) / total_assignments
        if total_assignments else 0.0
    )
    summary = {
        "protocol": "ground-truth detections; paper midpoint tracker; 50 px scaled from 640 px width",
        "sequences": results,
        "aggregate": {
            "sequence_count": len(results),
            "assignments": total_assignments,
            "weighted_track_purity": weighted_purity,
            "id_switches": sum(item["id_switches"] for item in results),
            "arriving_absolute_error": sum(item["absolute_count_error"]["Arriving"] for item in results),
            "leaving_absolute_error": sum(item["absolute_count_error"]["Leaving"] for item in results),
        },
    }
    (ROOT / "results").mkdir(exist_ok=True)
    output = ROOT / "results/tracking_evaluation.json"
    output.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

