"""Run YOLOv5s + DeepSORT on BEE22 held-out sequences and compute MOT metrics."""
from __future__ import annotations

import argparse
import csv
import json
import sqlite3  # load the Python environment's ICU/C++ runtime before Torch
import sys
import time
from collections import defaultdict
from pathlib import Path

import cv2
import motmetrics as mm
import numpy as np
import torch

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "vendor/yolov5"))
from models.common import DetectMultiBackend
from utils.augmentations import letterbox
from utils.general import non_max_suppression, scale_boxes
from deep_sort_realtime.deepsort_tracker import DeepSort


def read_gt(path: Path) -> dict[int, list[tuple[int, list[float]]]]:
    frames = defaultdict(list)
    with path.open() as f:
        for row in csv.reader(f):
            frame, identity = int(row[0]), int(row[1])
            x, y, w, h = map(float, row[2:6])
            frames[frame].append((identity, [x, y, w, h]))
    return frames


def predict(model, frame: np.ndarray, conf: float, iou: float) -> list[tuple[list[float], float]]:
    image = letterbox(frame, 640, stride=model.stride, auto=True)[0]
    image = image.transpose((2, 0, 1))[::-1]
    image = np.ascontiguousarray(image)
    tensor = torch.from_numpy(image).to(model.device).float() / 255.0
    with torch.inference_mode():
        result = model(tensor[None])
        det = non_max_suppression(result, conf, iou, classes=[0], max_det=300)[0]
    if not len(det):
        return []
    det = det.clone()
    det[:, :4] = scale_boxes(tensor.shape[1:], det[:, :4], frame.shape).round()
    output = []
    for x1, y1, x2, y2, score, _ in det.cpu().tolist():
        output.append(([x1, y1, x2 - x1, y2 - y1], score))
    return output


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--weights', type=Path, default=ROOT / 'runs/detector/yolov5s_seed50/weights/best.pt')
    parser.add_argument('--split', choices=['test', 'train'], default='test')
    parser.add_argument('--sequences', nargs='*')
    parser.add_argument('--conf', type=float, default=0.25)
    parser.add_argument('--iou', type=float, default=0.45)
    parser.add_argument('--output', type=Path, default=ROOT / 'runs/tracking')
    parser.add_argument('--roi', nargs=4, type=float, metavar=('X1', 'Y1', 'X2', 'Y2'))
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    model = DetectMultiBackend(str(args.weights), device=torch.device('cuda:0' if torch.cuda.is_available() else 'cpu'))
    model.warmup(imgsz=(1, 3, 640, 640))
    candidates = sorted((ROOT / 'data/BEE22' / args.split).glob('BEE22-*'))
    if args.sequences:
        candidates = [p for p in candidates if p.name in args.sequences]
    accumulators, names, seconds, frame_count = [], [], 0.0, 0
    all_counts = {}
    for sequence in candidates:
        tracker = DeepSort(max_age=30, n_init=3, max_cosine_distance=0.2, embedder='mobilenet', embedder_gpu=torch.cuda.is_available(), half=torch.cuda.is_available())
        gt = read_gt(sequence / 'gt/gt.txt')
        acc = mm.MOTAccumulator(auto_id=True)
        mot_rows = []
        enter, exit_, previous = 0, 0, {}
        images = sorted((sequence / 'img1').glob('*.jpg'))
        start = time.perf_counter()
        for image_path in images:
            frame_id = int(image_path.stem)
            frame = cv2.imread(str(image_path))
            if frame is None:
                raise ValueError(f'Cannot open {image_path}')
            detections = predict(model, frame, args.conf, args.iou)
            tracks = tracker.update_tracks([(box, confidence, 'bee') for box, confidence in detections], frame=frame)
            active = {}
            for track in tracks:
                if not track.is_confirmed() or track.time_since_update != 0:
                    continue
                xyxy = track.to_ltrb(orig=True, orig_strict=True)
                if xyxy is None:
                    continue
                x1, y1, x2, y2 = map(float, xyxy)
                if x2 <= x1 or y2 <= y1:
                    continue
                identity = int(track.track_id)
                active[identity] = [x1, y1, x2 - x1, y2 - y1]
                mot_rows.append([frame_id, identity, round(x1, 2), round(y1, 2), round(x2-x1, 2), round(y2-y1, 2), 1, -1, -1, -1])
            truth = gt.get(frame_id, [])
            ids, truth_boxes = zip(*truth) if truth else ([], [])
            acc.update(list(ids), list(active), mm.distances.iou_matrix(truth_boxes, list(active.values()), max_iou=0.5))
            if args.roi:
                x1, y1, x2, y2 = args.roi
                centers = {i: (b[0]+b[2]/2, b[1]+b[3]/2) for i,b in active.items()}
                inside = lambda p: x1 <= p[0] <= x2 and y1 <= p[1] <= y2
                for i, point in centers.items():
                    if i in previous:
                        if not inside(previous[i]) and inside(point): enter += 1
                        elif inside(previous[i]) and not inside(point): exit_ += 1
                previous = centers
        elapsed = time.perf_counter() - start
        seconds += elapsed
        frame_count += len(images)
        with (args.output / f'{sequence.name}.txt').open('w', newline='') as f:
            csv.writer(f).writerows(mot_rows)
        accumulators.append(acc)
        names.append(sequence.name)
        all_counts[sequence.name] = {'frames': len(images), 'seconds': elapsed, 'enter': enter, 'exit': exit_, 'tracks_output': len(mot_rows)}
        print(f'{sequence.name}: {len(images)} frames, {elapsed:.1f}s, {len(mot_rows)} track boxes', flush=True)
    mh = mm.metrics.create()
    metrics = ['mota', 'motp', 'idf1', 'precision', 'recall', 'num_frames', 'num_objects', 'num_switches', 'num_misses', 'num_false_positives']
    summary = mh.compute_many(accumulators, names=names, metrics=metrics, generate_overall=True)
    result = {}
    for name, row in summary.iterrows():
        item = {key: (None if np.isnan(float(value)) else float(value)) for key, value in row.items()}
        item['motp_iou'] = None if item['motp'] is None else 1 - item['motp']
        result[name] = item
    report = {'weights': str(args.weights), 'conf': args.conf, 'iou_nms': args.iou, 'mot_iou_matching_threshold': 0.5, 'fps_including_detection_tracking_and_io': frame_count/seconds, 'roi_xyxy': args.roi, 'counts': all_counts, 'motmetrics': result, 'note': 'MOTP in motmetrics is mean distance (1-IoU); motp_iou is mean matched IoU. ROI counts have no ground-truth event labels.'}
    (args.output / 'results.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
