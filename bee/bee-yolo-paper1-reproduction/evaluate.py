"""Evaluate one checkpoint exactly once on the public test split."""
from __future__ import annotations

import argparse
import importlib.metadata
import os
import shutil
import subprocess
import matplotlib
import json
import platform
from pathlib import Path
import sys
import sqlite3  # load conda ICU before Torch selects the system libstdc++

import torch
from download_assets import sha256

ROOT = Path(__file__).resolve().parent


def environment() -> dict:
    return {
        'python': platform.python_version(),
        'torch': torch.__version__,
        'cuda': torch.version.cuda,
        'gpu': torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
        'ultralytics': importlib.metadata.version('ultralytics'),
        'yolov5_source': 'v7.0 (tag commit 915bbf294bb74c859f0b41f1c23bc395014ea679)',
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--model', choices=['yolov5m', 'yolo26m'], required=True)
    parser.add_argument('--tag', required=True)
    parser.add_argument('--weights', type=Path, required=True)
    parser.add_argument('--batch', type=int, default=16)
    parser.add_argument('--imgsz', type=int, default=416)
    parser.add_argument('--workers', type=int, default=4, help='validation data loader workers; use 0 if multiprocessing stalls')
    args = parser.parse_args()
    weights = args.weights.resolve()
    if not weights.is_file():
        parser.error(f'missing weights: {weights}')
    output = ROOT / 'runs/eval' / args.tag
    if output.exists():
        parser.error(f'evaluation directory exists: {output}')
    if not (ROOT / 'dataset_audit.json').is_file():
        parser.error('run prepare_dataset.py first')
    if os.environ.get('BEE_EVAL_CHILD') != '1':
        log_path = ROOT / 'runs/eval' / f'{args.tag}.log'
        if log_path.exists():
            parser.error(f'evaluation log exists: {log_path}')
        log_path.parent.mkdir(parents=True, exist_ok=True)
        env = os.environ.copy()
        env['BEE_EVAL_CHILD'] = '1'
        env['LD_LIBRARY_PATH'] = str(Path(sys.base_prefix) / 'lib') + ':' + env.get('LD_LIBRARY_PATH', '')
        with log_path.open('w') as log:
            process = subprocess.Popen([sys.executable, str(Path(__file__).resolve()), *sys.argv[1:]],
                                       cwd=ROOT, env=env, stdout=subprocess.PIPE,
                                       stderr=subprocess.STDOUT, text=True, bufsize=1)
            assert process.stdout is not None
            for line in process.stdout:
                print(line, end='', flush=True)
                log.write(line)
                log.flush()
            code = process.wait()
        if code:
            raise SystemExit(code)
        return
    data = ROOT / 'dataset.yaml'
    common = {
        'model': args.model,
        'weights': str(weights),
        'weights_sha256': sha256(weights),
        'weights_bytes': weights.stat().st_size,
        'dataset_sha256': json.loads((ROOT / 'dataset_audit.json').read_text())['sha256'],
        'test_images': 996,
        'test_boxes': 1343,
        'imgsz': args.imgsz,
        'batch': args.batch,
        'workers': args.workers,
        'evaluation': {'split': 'test', 'conf': 0.001, 'nms_iou': 0.6, 'max_det': 300, 'half': torch.cuda.is_available()},
        'environment': environment(),
    }
    if args.model == 'yolov5m':
        font_dir = ROOT / 'cache'
        font_dir.mkdir(exist_ok=True)
        shutil.copyfile(Path(matplotlib.get_data_path()) / 'fonts/ttf/DejaVuSans.ttf', font_dir / 'Arial.ttf')
        os.environ['YOLOV5_CONFIG_DIR'] = str(font_dir)
        sys.path.insert(0, str(ROOT / 'vendor/yolov5'))
        import val
        result, _, timing = val.run(
            data=str(data), weights=str(weights), batch_size=args.batch,
            imgsz=args.imgsz, task='test', device='0' if torch.cuda.is_available() else 'cpu',
            project=ROOT / 'runs/eval', name=args.tag, plots=True,
            half=torch.cuda.is_available(), workers=args.workers, conf_thres=0.001, iou_thres=0.6, max_det=300,
        )
        p, r, map50, map5095 = result[:4]
        speed = dict(zip(['preprocess', 'inference', 'nms'], timing))
        checkpoint = torch.load(weights, map_location='cpu')
        network = checkpoint.get('ema') or checkpoint.get('model')
        common['parameter_count'] = sum(parameter.numel() for parameter in network.parameters())
    else:
        from ultralytics import YOLO
        model = YOLO(str(weights))
        metric = model.val(
            data=str(data), split='test', imgsz=args.imgsz, batch=args.batch,
            device=0 if torch.cuda.is_available() else 'cpu',
            project=str(ROOT / 'runs/eval'), name=args.tag,
            workers=args.workers, plots=True, save_json=False, conf=0.001, iou=0.6,
            max_det=300, half=torch.cuda.is_available(),
        )
        p, r = metric.box.mp, metric.box.mr
        map50, map5095 = metric.box.map50, metric.box.map
        speed = metric.speed
        common['parameter_count'] = sum(parameter.numel() for parameter in model.model.parameters())
    common['metrics'] = {
        'precision': float(p), 'recall': float(r),
        'map50': float(map50), 'map50_95': float(map5095),
        'speed_ms_per_image': {k: float(v) for k, v in speed.items()},
    }
    output.mkdir(parents=True, exist_ok=True)
    (output / 'metrics.json').write_text(json.dumps(common, indent=2, ensure_ascii=False) + '\n')
    print(json.dumps(common, indent=2, ensure_ascii=False))


if __name__ == '__main__':
    main()
