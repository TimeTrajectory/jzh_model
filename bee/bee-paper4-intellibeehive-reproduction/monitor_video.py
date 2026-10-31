#!/usr/bin/env python3
"""Detect, track and count bees crossing hive-entrance trigger lines in video."""
from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path

import cv2

from inference import Detector, draw_detections
from tracking import Detection, IntelliBeeTracker

ROOT = Path(__file__).resolve().parent


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True)
    parser.add_argument("--weights", default=str(ROOT / "runs/train/pollen_yolov7_tiny_e100/weights/best.pt"))
    parser.add_argument("--output", default=str(ROOT / "runs/video/monitored.mp4"))
    parser.add_argument("--confidence", type=float, default=0.25)
    parser.add_argument("--device", default="0")
    args = parser.parse_args()

    capture = cv2.VideoCapture(args.source)
    if not capture.isOpened():
        raise FileNotFoundError(args.source)
    width = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = capture.get(cv2.CAP_PROP_FPS) or 10.0
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    writer = cv2.VideoWriter(str(output), cv2.VideoWriter_fourcc(*"mp4v"), fps, (width, height))
    detector = Detector(args.weights, args.device)
    tracker = IntelliBeeTracker(width, height)
    pollen_crossings = 0
    rows = []
    frame_index = 0
    while True:
        ok, frame = capture.read()
        if not ok:
            break
        frame_index += 1
        detections = detector.predict(frame, args.confidence)
        boxes = [Detection(*item["bbox"], confidence=item["confidence"]) for item in detections]
        before = len(tracker.events)
        profiles = tracker.update(boxes, frame_index)
        new_events = tracker.events[before:]
        for event in new_events:
            profile = next((p for p in profiles if p.track_id == event["track_id"]), None)
            if profile:
                # Match the event midpoint to the nearest current model detection.
                nearest = min(detections, key=lambda d: (profile.midpoint[0]-(d["bbox"][0]+d["bbox"][2])/2)**2 + (profile.midpoint[1]-(d["bbox"][1]+d["bbox"][3])/2)**2)
                if nearest["class_id"] == 1:
                    pollen_crossings += 1
        annotated = draw_detections(frame, detections)
        for y, color in [(int(tracker.upper), (255, 180, 0)), (int(tracker.lower), (255, 180, 0))]:
            cv2.line(annotated, (0, y), (width, y), color, 2)
        text = f"Arriving {tracker.counts['Arriving']}  Leaving {tracker.counts['Leaving']}  Pollen {pollen_crossings}"
        cv2.putText(annotated, text, (15, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (20, 20, 230), 2)
        writer.write(annotated)
        rows.append({"frame": frame_index, **tracker.counts, "pollen_crossings": pollen_crossings, "detections": len(detections)})
    capture.release()
    writer.release()
    csv_path = output.with_suffix(".csv")
    with csv_path.open("w", newline="", encoding="utf-8-sig") as handle:
        writer_csv = csv.DictWriter(handle, fieldnames=list(rows[0]) if rows else ["frame"])
        writer_csv.writeheader(); writer_csv.writerows(rows)
    summary = {"video": str(output), "frames": frame_index, "counts": tracker.counts, "pollen_crossings": pollen_crossings, "events": tracker.events}
    output.with_suffix(".json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

