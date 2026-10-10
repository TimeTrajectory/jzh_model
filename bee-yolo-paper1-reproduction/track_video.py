"""Qualitative ByteTrack demo on a continuous video using a trained YOLO26 bee detector."""
from __future__ import annotations

import sqlite3  # load conda ICU before Torch in this environment
import argparse
import csv
import json
from pathlib import Path
import cv2
from ultralytics import YOLO

ROOT = Path(__file__).resolve().parent


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--video', type=Path, required=True)
    parser.add_argument('--weights', type=Path, default=ROOT / 'runs/yolo26m_416/weights/best.pt')
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--max-frames', type=int, default=0)
    args = parser.parse_args()
    video, weights, output = args.video.resolve(), args.weights.resolve(), args.output.resolve()
    if not video.is_file() or not weights.is_file():
        parser.error('video or trained weights missing')
    if output.exists():
        parser.error(f'{output} exists')
    cap = cv2.VideoCapture(str(video))
    if not cap.isOpened():
        raise RuntimeError('cannot open video')
    fps = cap.get(cv2.CAP_PROP_FPS)
    size = (int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)))
    cap.release()
    if fps <= 0 or min(size) <= 0:
        raise RuntimeError('invalid video metadata')
    model = YOLO(str(weights))
    output.mkdir(parents=True)
    writer = cv2.VideoWriter(str(output / 'annotated_tracks.mp4'),
                             cv2.VideoWriter_fourcc(*'mp4v'), fps, size)
    if not writer.isOpened():
        raise RuntimeError('cannot open output video')
    frame_count = 0
    row_count = 0
    try:
        with (output / 'tracks.csv').open('w', newline='') as file:
            csv_writer = csv.writer(file)
            csv_writer.writerow(['frame_index', 'time_seconds', 'temporary_track_id', 'confidence',
                                 'center_x', 'center_y', 'x1', 'y1', 'x2', 'y2'])
            results = model.track(source=str(video), stream=True, persist=True,
                                  tracker='bytetrack.yaml', imgsz=416, conf=0.1, iou=0.7,
                                  verbose=False)
            for frame_index, result in enumerate(results):
                if args.max_frames and frame_index >= args.max_frames:
                    break
                boxes = result.boxes
                if boxes is not None and boxes.id is not None:
                    ids = boxes.id.int().cpu().tolist()
                    xyxys = boxes.xyxy.cpu().tolist()
                    confs = boxes.conf.cpu().tolist()
                    for track_id, xyxy, confidence in zip(ids, xyxys, confs):
                        x1, y1, x2, y2 = xyxy
                        csv_writer.writerow([frame_index, f'{frame_index / fps:.3f}', track_id,
                                             f'{confidence:.5f}', f'{(x1+x2)/2:.2f}',
                                             f'{(y1+y2)/2:.2f}', f'{x1:.2f}', f'{y1:.2f}',
                                             f'{x2:.2f}', f'{y2:.2f}'])
                        row_count += 1
                writer.write(result.plot())
                frame_count += 1
    finally:
        writer.release()
    summary = {'video': str(video), 'weights': str(weights), 'tracker': 'bytetrack.yaml',
               'fps': fps, 'frames': frame_count, 'track_rows': row_count,
               'note': 'IDs are temporary associations. No IDF1, MOTA, or entry/exit accuracy without ground truth.'}
    (output / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
