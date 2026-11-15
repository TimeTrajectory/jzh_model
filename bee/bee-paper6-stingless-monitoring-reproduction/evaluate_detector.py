#!/usr/bin/env python3
"""Evaluate one checkpoint on validation or held-out test sequences."""
from pathlib import Path
import argparse,json,re,subprocess,time
ROOT=Path(__file__).resolve().parent
p=argparse.ArgumentParser(); p.add_argument('--weights',type=Path,default=ROOT/'runs/train/backup/yolov3-tiny-bee_final.weights'); p.add_argument('--split',choices=('val','test'),default='test'); a=p.parse_args()
data=ROOT/'data/bee22_darknet'/('bee.data' if a.split=='val' else 'bee_test.data')
cmd=[str(ROOT/'vendor/darknet/darknet'),'detector','map',str(data),str(ROOT/'configs/yolov3-tiny-bee.cfg'),str(a.weights),'-iou_thresh','0.5','-points','101']
t=time.perf_counter(); r=subprocess.run(cmd,cwd=ROOT,text=True,capture_output=True); elapsed=time.perf_counter()-t; log=r.stdout+'\n'+r.stderr
(ROOT/'results').mkdir(exist_ok=True); (ROOT/'results'/f'detector_{a.split}.log').write_text(log)
if r.returncode: raise SystemExit(log[-4000:])
def g(pattern):
 m=re.search(pattern,log,re.I); return float(m.group(1)) if m else None
result={'split':a.split,'weights':str(a.weights),'elapsed_seconds':elapsed,'map50':g(r'mAP@0\.50[^=]*=\s*([0-9.]+)'),'precision':g(r'precision\s*=\s*([0-9.]+)'),'recall':g(r'recall\s*=\s*([0-9.]+)'),'f1':g(r'F1-score\s*=\s*([0-9.]+)'),'tp':g(r'TP\s*=\s*([0-9.]+)'),'fp':g(r'FP\s*=\s*([0-9.]+)'),'fn':g(r'FN\s*=\s*([0-9.]+)')}
(ROOT/'results'/f'detector_{a.split}_metrics.json').write_text(json.dumps(result,indent=2)+'\n'); print(json.dumps(result,indent=2))

