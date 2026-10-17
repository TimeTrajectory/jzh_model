"""Produce the paper's sampled-frame bee counts and timestamp CSV from a video."""
from __future__ import annotations

import sqlite3  # load conda ICU before Torch in this environment
import argparse
import csv
import json
import math
import os
from pathlib import Path
import shutil

import cv2
import torch

ROOT = Path(__file__).resolve().parent


def load_model(model_kind: str, weights: Path, confidence: float, iou: float):
    if model_kind == 'yolov5m':
        import matplotlib
        font_dir = ROOT / 'cache'
        font_dir.mkdir(exist_ok=True)
        shutil.copyfile(Path(matplotlib.get_data_path()) / 'fonts/ttf/DejaVuSans.ttf', font_dir / 'Arial.ttf')
        os.environ['YOLOV5_CONFIG_DIR'] = str(font_dir)
        model = torch.hub.load(str(ROOT / 'vendor/yolov5'), 'custom', path=str(weights),
                               source='local', device='cuda:0' if torch.cuda.is_available() else 'cpu', verbose=False)
        model.conf, model.iou = confidence, iou
        def predict(frame):
            height, width = frame.shape[:2]
            resized = cv2.resize(frame, (416, 416), interpolation=cv2.INTER_CUBIC)
            rgb = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
            result = model(rgb, size=416)
            return [[float(row[0])*width/416, float(row[1])*height/416,
                     float(row[2])*width/416, float(row[3])*height/416, float(row[4])]
                    for row in result.xyxy[0].cpu().numpy()]
        return predict
    from ultralytics import YOLO
    model = YOLO(str(weights))
    def predict(frame):
        result = model.predict(frame, imgsz=416, conf=confidence, iou=iou,
                               device=0 if torch.cuda.is_available() else 'cpu', verbose=False)[0]
        boxes = result.boxes
        return [list(map(float, (*xyxy, conf))) for xyxy, conf in zip(boxes.xyxy.cpu().numpy(), boxes.conf.cpu().numpy())]
    return predict


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--video', type=Path, required=True)
    parser.add_argument('--weights', type=Path, help='defaults to the author model or trained YOLO26m')
    parser.add_argument('--model', choices=['yolov5m', 'yolo26m'], default='yolov5m')
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--stride', type=int, default=0, help='0 uses the author app interval floor(FPS)/2 frames')
    parser.add_argument('--confidence', type=float, default=0.30)
    parser.add_argument('--iou', type=float, default=0.45)
    parser.add_argument('--max-frames', type=int, default=0, help='0 means the full video')
    args = parser.parse_args()
    default_weights = ROOT / ('weights/author_custom_yolov5m.pt' if args.model == 'yolov5m' else 'runs/yolo26m_416/weights/best.pt')
    video, weights, output = args.video.resolve(), (args.weights or default_weights).resolve(), args.output.resolve()
    if args.stride < 0 or not 0 < args.confidence < 1 or not 0 < args.iou < 1:
        parser.error('stride must be nonnegative and thresholds must be between 0 and 1')
    if not video.is_file() or not weights.is_file():
        parser.error('video or weights file missing')
    if output.exists():
        parser.error(f'{output} exists; choose a new output directory')
    cap = cv2.VideoCapture(str(video))
    if not cap.isOpened():
        raise RuntimeError(f'cannot open video: {video}')
    fps = cap.get(cv2.CAP_PROP_FPS)
    width, height = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    if not (fps > 0 and width > 0 and height > 0):
        raise RuntimeError('video has invalid FPS or dimensions')
    stride = args.stride or max(1, int(fps) // 2)
    predict = load_model(args.model, weights, args.confidence, args.iou)
    output.mkdir(parents=True)
    writer = cv2.VideoWriter(str(output / 'annotated.mp4'), cv2.VideoWriter_fourcc(*'mp4v'), fps / stride, (width, height))
    if not writer.isOpened():
        raise RuntimeError('cannot open annotated video writer')
    count_rows = 0
    detection_rows = 0
    frame_index = 0
    per_second_max = {}
    try:
        with (output / 'counts.csv').open('w', newline='') as count_file, (output / 'detections.csv').open('w', newline='') as det_file:
            counts = csv.writer(count_file)
            detections = csv.writer(det_file)
            counts.writerow(['frame_index', 'time_seconds', 'time_hh_mm_ss', 'visible_bee_count'])
            detections.writerow(['frame_index', 'time_seconds', 'detection_index', 'confidence', 'x1', 'y1', 'x2', 'y2'])
            while True:
                ok, frame = cap.read()
                if not ok or (args.max_frames and frame_index >= args.max_frames):
                    break
                if frame_index % stride == 0:
                    boxes = predict(frame)
                    seconds = frame_index / fps
                    hh = int(seconds // 3600)
                    mm = int((seconds % 3600) // 60)
                    ss = seconds % 60
                    stamp = f'{hh:02d}:{mm:02d}:{ss:06.3f}'
                    counts.writerow([frame_index, f'{seconds:.3f}', stamp, len(boxes)])
                    second_index = int(seconds)
                    per_second_max[second_index] = max(per_second_max.get(second_index, 0), len(boxes))
                    count_rows += 1
                    for j, (x1, y1, x2, y2, conf) in enumerate(boxes):
                        detections.writerow([frame_index, f'{seconds:.3f}', j, f'{conf:.5f}',
                                             f'{x1:.2f}', f'{y1:.2f}', f'{x2:.2f}', f'{y2:.2f}'])
                        detection_rows += 1
                        cv2.rectangle(frame, (round(x1), round(y1)), (round(x2), round(y2)), (0, 215, 255), 2)
                        cv2.putText(frame, f'bee {conf:.2f}', (round(x1), max(20, round(y1)-5)),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 215, 255), 1)
                    cv2.putText(frame, f'{stamp}   visible bees: {len(boxes)}', (10, 28),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                    writer.write(frame)
                frame_index += 1
    finally:
        writer.release()
        cap.release()
    with (output / 'presence_by_second.csv').open('w', newline='') as second_file:
        by_second = csv.writer(second_file)
        by_second.writerow(['second', 'detected_flag', 'max_visible_bee_count'])
        for second in range(math.ceil(frame_index / fps)):
            maximum = per_second_max.get(second, 0)
            by_second.writerow([second, int(maximum > 0), maximum])
    summary = {'video': str(video), 'model': args.model, 'weights': str(weights),
               'fps': fps, 'stride': stride, 'sampled_fps': fps / stride,
               'confidence': args.confidence, 'iou': args.iou, 'frames_read': frame_index,
               'frames_sampled': count_rows, 'detections': detection_rows,
               'note': 'Counts are visible detections per sampled frame, not unique bees or hive entry events.'}
    (output / 'report.json').write_text(json.dumps(summary, indent=2) + '\n')
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
