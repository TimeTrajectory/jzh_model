"""Fixed-threshold error audit of author YOLOv5m on public test images."""
from __future__ import annotations

import sqlite3  # load conda ICU before Torch in this environment
import argparse
from collections import Counter
import csv
import json
import os
from pathlib import Path
import shutil

import cv2
import matplotlib
import numpy as np
import torch

ROOT = Path(__file__).resolve().parent


def iou(a, b):
    x1, y1 = max(a[0], b[0]), max(a[1], b[1])
    x2, y2 = min(a[2], b[2]), min(a[3], b[3])
    intersection = max(0, x2-x1) * max(0, y2-y1)
    area_a = max(0, a[2]-a[0]) * max(0, a[3]-a[1])
    area_b = max(0, b[2]-b[0]) * max(0, b[3]-b[1])
    union = area_a + area_b - intersection
    return intersection / union if union else 0


def size_bin(box):
    area = (box[2]-box[0]) * (box[3]-box[1])
    return 'small' if area < 32**2 else ('medium' if area < 96**2 else 'large')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--model', choices=['yolov5m', 'yolo26m'], default='yolov5m')
    parser.add_argument('--weights', type=Path, help='checkpoint to audit')
    parser.add_argument('--output', type=Path, default=ROOT / 'runs/error_analysis_author')
    parser.add_argument('--confidence', type=float, default=0.25)
    parser.add_argument('--iou', type=float, default=0.5)
    args = parser.parse_args()
    output = args.output.resolve()
    weights = (args.weights or ROOT / ('weights/author_custom_yolov5m.pt' if args.model == 'yolov5m' else 'runs/yolo26m_416/weights/best.pt')).resolve()
    if not weights.is_file():
        parser.error(f'missing weights: {weights}')
    if output.exists():
        parser.error(f'{output} exists')
    font_dir = ROOT / 'cache'
    font_dir.mkdir(exist_ok=True)
    shutil.copyfile(Path(matplotlib.get_data_path()) / 'fonts/ttf/DejaVuSans.ttf', font_dir / 'Arial.ttf')
    os.environ['YOLOV5_CONFIG_DIR'] = str(font_dir)
    if args.model == 'yolov5m':
        model = torch.hub.load(str(ROOT / 'vendor/yolov5'), 'custom', path=str(weights),
                               source='local', device='cuda:0' if torch.cuda.is_available() else 'cpu', verbose=False)
        model.conf = args.confidence
        model.iou = 0.45
        def predict(frame):
            result = model(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB), size=416)
            return result.xyxy[0].cpu().numpy().tolist()
    else:
        from ultralytics import YOLO
        model = YOLO(str(weights))
        def predict(frame):
            result = model.predict(frame, imgsz=416, conf=args.confidence, iou=0.45,
                                   device=0 if torch.cuda.is_available() else 'cpu', verbose=False)[0]
            return [[*xyxy, conf, 0] for xyxy, conf in zip(result.boxes.xyxy.cpu().numpy().tolist(),
                                                            result.boxes.conf.cpu().numpy().tolist())]
    output.mkdir(parents=True)
    images = sorted((ROOT / 'dataset/images/test').glob('*.jpg'))
    stats = {key: Counter() for key in ('small', 'medium', 'large')}
    false_negative, false_positive = [], []
    visual_candidates = []
    for index, image_path in enumerate(images):
        frame = cv2.imread(str(image_path))
        if frame is None:
            raise RuntimeError(f'cannot read {image_path}')
        h, w = frame.shape[:2]
        label_path = ROOT / 'dataset/labels/test' / (image_path.stem + '.txt')
        gt = []
        for line in label_path.read_text().splitlines():
            cls, xc, yc, bw, bh = map(float, line.split())
            if cls != 0:
                raise ValueError('unexpected class')
            gt.append([(xc-bw/2)*w, (yc-bh/2)*h, (xc+bw/2)*w, (yc+bh/2)*h])
        preds = predict(frame)
        preds.sort(key=lambda row: -row[4])
        matched = set()
        unmatched_preds = []
        for pred in preds:
            candidates = [(iou(pred, box), j) for j, box in enumerate(gt) if j not in matched]
            best_iou, best_j = max(candidates, default=(0, -1))
            if best_iou >= args.iou:
                matched.add(best_j)
            else:
                unmatched_preds.append(pred)
        misses = [j for j in range(len(gt)) if j not in matched]
        for j, box in enumerate(gt):
            group = size_bin(box)
            stats[group]['gt'] += 1
            if j in matched:
                stats[group]['matched'] += 1
            else:
                false_negative.append([image_path.name, group, *[round(v, 2) for v in box]])
        for pred in unmatched_preds:
            false_positive.append([image_path.name, round(pred[4], 5), *[round(v, 2) for v in pred[:4]]])
        if misses or unmatched_preds:
            visual_candidates.append((len(misses), len(unmatched_preds), image_path, gt, preds, misses))
        if (index + 1) % 100 == 0:
            print(f'{index+1}/{len(images)}', flush=True)
    summary = {'model': args.model, 'weights': str(weights), 'test_images': len(images), 'confidence': args.confidence, 'matching_iou': args.iou,
               'size_rule': 'COCO-style pixel area on 416x416 images: small <32^2, medium <96^2, large >=96^2',
               'size_recall': {key: {'gt': stats[key]['gt'], 'matched': stats[key]['matched'],
                                    'recall': stats[key]['matched']/stats[key]['gt'] if stats[key]['gt'] else None}
                               for key in stats},
               'false_negative_boxes': len(false_negative), 'false_positive_boxes': len(false_positive),
               'note': 'This fixed-threshold IoU=0.5 recall is not mAP.'}
    (output / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    with (output / 'false_negatives.csv').open('w', newline='') as f:
        wr = csv.writer(f);wr.writerow(['image', 'size', 'x1', 'y1', 'x2', 'y2']);wr.writerows(false_negative)
    with (output / 'false_positives.csv').open('w', newline='') as f:
        wr = csv.writer(f);wr.writerow(['image', 'confidence', 'x1', 'y1', 'x2', 'y2']);wr.writerows(false_positive)
    visual_candidates.sort(key=lambda row: (row[0], row[1]), reverse=True)
    for k, (_, _, image_path, gt, preds, misses) in enumerate(visual_candidates[:8], 1):
        frame = cv2.imread(str(image_path))
        for j, box in enumerate(gt):
            x1, y1, x2, y2 = map(round, box)
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255) if j in misses else (0, 180, 0), 2)
        for pred in preds:
            x1, y1, x2, y2 = map(round, pred[:4])
            cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 170, 0), 1)
        cv2.imwrite(str(output / f'error_{k:02d}.jpg'), frame)
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
