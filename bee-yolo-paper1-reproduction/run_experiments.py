"""Run the prescribed 100-epoch experiment with logged settings."""
from __future__ import annotations

import argparse
import os
import shutil
import matplotlib
import json
from pathlib import Path
import subprocess
import sys
import time

from download_assets import sha256

ROOT = Path(__file__).resolve().parent


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--model', choices=['yolov5m', 'yolo26m'], required=True)
    parser.add_argument('--batch', type=int, default=16)
    parser.add_argument('--epochs', type=int, default=100)
    parser.add_argument('--imgsz', type=int, default=416)
    parser.add_argument('--seed', type=int, default=42)
    parser.add_argument('--device', default='auto', help='auto, cpu, or a CUDA index such as 0')
    parser.add_argument('--weights', type=Path)
    parser.add_argument('--resume', action='store_true', help='continue an interrupted run from weights/last.pt')
    args = parser.parse_args()
    if args.device == 'auto':
        import torch
        device = '0' if torch.cuda.is_available() else 'cpu'
    else:
        device = args.device
    default_weights = ROOT / 'weights' / (args.model + '.pt')
    weights = (args.weights or default_weights).resolve()
    name = f'{args.model}_{args.imgsz}'
    output = ROOT / 'runs' / name
    if output.exists() and not args.resume:
        parser.error(f'{output} exists; inspect the previous run before rerunning')
    last = output / 'weights/last.pt'
    if args.resume and not last.is_file():
        parser.error(f'missing resume checkpoint: {last}')
    if args.resume and (output / 'reproduction_config.json').is_file():
        previous = json.loads((output / 'reproduction_config.json').read_text())
        if previous.get('exit_code') == 0:
            parser.error(f'{output} has already completed successfully')
    if not (ROOT / 'dataset_audit.json').exists():
        parser.error('run prepare_dataset.py first')
    if not weights.is_file():
        parser.error(f'missing pretrained weights: {weights}; see README.md')
    if args.resume and args.model == 'yolov5m':
        command = [sys.executable, str(ROOT / 'vendor/yolov5/train.py'), '--resume', str(last)]
    elif args.resume:
        command = ['yolo', 'detect', 'train', 'model=' + str(last), 'resume=True']
    elif args.model == 'yolov5m':
        command = [sys.executable, str(ROOT / 'vendor/yolov5/train.py'),
                   '--data', str(ROOT / 'dataset.yaml'), '--weights', str(weights),
                   '--epochs', str(args.epochs), '--batch-size', str(args.batch),
                   '--imgsz', str(args.imgsz), '--seed', str(args.seed),
                   '--workers', '4', '--device', device,
                   '--project', str(ROOT / 'runs'), '--name', name, '--exist-ok']
    else:
        command = ['yolo', 'detect', 'train',
                   'model=' + str(weights), 'data=' + str(ROOT / 'dataset.yaml'),
                   'epochs=' + str(args.epochs), 'batch=' + str(args.batch),
                   'imgsz=' + str(args.imgsz), 'seed=' + str(args.seed),
                   'workers=4', 'device=' + device, 'project=' + str(ROOT / 'runs'),
                   'name=' + name, 'exist_ok=True']
    output.mkdir(parents=True, exist_ok=args.resume)
    if args.resume:
        metadata = json.loads((output / 'reproduction_config.json').read_text())
        metadata.setdefault('resume_attempts', []).append({'command': command, 'started_unix': time.time(),
                                                           'checkpoint_sha256': sha256(last)})
    else:
        metadata = {'model': args.model, 'args': vars(args) | {'weights': str(weights)},
                    'pretrained_sha256': sha256(weights), 'command': command,
                    'started_unix': time.time()}
    (output / 'reproduction_config.json').write_text(json.dumps(metadata, indent=2, default=str) + '\n')
    with (output / 'train.log').open('a' if args.resume else 'w') as log:
        env = os.environ.copy()
        font_dir = ROOT / 'cache'
        font_dir.mkdir(exist_ok=True)
        shutil.copyfile(Path(matplotlib.get_data_path()) / 'fonts/ttf/DejaVuSans.ttf', font_dir / 'Arial.ttf')
        env['YOLOV5_CONFIG_DIR'] = str(font_dir)
        env["LD_LIBRARY_PATH"] = str(Path(sys.base_prefix) / "lib") + ":" + env.get("LD_LIBRARY_PATH", "")
        proc = subprocess.Popen(command, cwd=ROOT, env=env, stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT, text=True, bufsize=1)
        assert proc.stdout is not None
        for line in proc.stdout:
            print(line, end='', flush=True)
            log.write(line)
            log.flush()
        code = proc.wait()
    metadata['finished_unix'] = time.time()
    metadata['exit_code'] = code
    if args.resume:
        metadata['resume_attempts'][-1]['finished_unix'] = metadata['finished_unix']
        metadata['resume_attempts'][-1]['exit_code'] = code
    (output / 'reproduction_config.json').write_text(json.dumps(metadata, indent=2, default=str) + '\n')
    if code:
        raise SystemExit(code)
    best = output / 'weights/best.pt'
    if not best.is_file():
        raise RuntimeError(f'training exited successfully but {best} is absent')
    print(f'best.pt SHA256: {sha256(best)}')


if __name__ == '__main__':
    main()
