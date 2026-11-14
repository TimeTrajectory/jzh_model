#!/usr/bin/env python3
"""Run Darknet's native AP evaluation on the held-out BEE22 test sequences."""
from pathlib import Path
import argparse, json, re, subprocess, time

ROOT=Path(__file__).resolve().parent
p=argparse.ArgumentParser(); p.add_argument('--weights',type=Path,default=ROOT/'runs/train/backup/yolov4-bee_best.weights')
a=p.parse_args()
cmd=[str(ROOT/'vendor/darknet/darknet'),'detector','map',str(ROOT/'data/bee22_darknet/bee_test.data'),str(ROOT/'configs/yolov4-bee.cfg'),str(a.weights),'-iou_thresh','0.5','-points','101']
t=time.perf_counter(); run=subprocess.run(cmd,cwd=ROOT,text=True,capture_output=True); elapsed=time.perf_counter()-t
log=run.stdout+'\n'+run.stderr
(ROOT/'results').mkdir(exist_ok=True); (ROOT/'results/detector_evaluation.log').write_text(log)
if run.returncode: raise SystemExit(log[-4000:])
def number(pattern):
    m=re.search(pattern,log,re.I); return float(m.group(1)) if m else None
result={
 'weights':str(a.weights),'images':762,'labels':12205,'iou_threshold':0.5,'elapsed_seconds':elapsed,
 'map50':number(r'mAP@0\.50[^=]*=\s*([0-9.]+)'),
 'precision':number(r'precision\s*=\s*([0-9.]+)'),
 'recall':number(r'recall\s*=\s*([0-9.]+)'),
 'f1':number(r'F1-score\s*=\s*([0-9.]+)'),
 'tp':number(r'TP\s*=\s*([0-9.]+)'), 'fp':number(r'FP\s*=\s*([0-9.]+)'), 'fn':number(r'FN\s*=\s*([0-9.]+)')}
(ROOT/'results/detector_metrics.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
