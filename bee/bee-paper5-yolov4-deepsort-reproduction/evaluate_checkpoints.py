#!/usr/bin/env python3
"""Compare YOLOv4 checkpoints on validation data and select the best one."""
from pathlib import Path
import argparse,json,re,shutil,subprocess,time
ROOT=Path(__file__).resolve().parent
p=argparse.ArgumentParser()
p.add_argument('weights',nargs='*',type=Path)
p.add_argument('--split',choices=('val','test'),default='val',
               help='Use val for model selection. Test is only for diagnostic use.')
p.add_argument('--no-copy-best',action='store_true')
a=p.parse_args()
weights=a.weights or sorted((ROOT/'runs/train/backup').glob('*.weights'))
data_file=ROOT/'data/bee22_darknet'/('bee.data' if a.split=='val' else 'bee_test.data')
records=[]
for weight in weights:
    cmd=[str(ROOT/'vendor/darknet/darknet'),'detector','map',str(data_file),str(ROOT/'configs/yolov4-bee.cfg'),str(weight),'-iou_thresh','0.5','-points','101']
    start=time.perf_counter(); run=subprocess.run(cmd,cwd=ROOT,text=True,capture_output=True); elapsed=time.perf_counter()-start; log=run.stdout+'\n'+run.stderr
    (ROOT/'results'/f'{weight.stem}_{a.split}.log').write_text(log)
    if run.returncode: print(log[-2000:]); continue
    def get(pat):
        m=re.search(pat,log,re.I); return float(m.group(1)) if m else None
    rec={'split':a.split,'weight':str(weight),'elapsed_seconds':elapsed,'map50':get(r'mAP@0\.50[^=]*=\s*([0-9.]+)'), 'precision':get(r'precision\s*=\s*([0-9.]+)'), 'recall':get(r'recall\s*=\s*([0-9.]+)'), 'f1':get(r'F1-score\s*=\s*([0-9.]+)'), 'tp':get(r'TP\s*=\s*([0-9.]+)'), 'fp':get(r'FP\s*=\s*([0-9.]+)'), 'fn':get(r'FN\s*=\s*([0-9.]+)')}
    records.append(rec); print(json.dumps(rec))
(ROOT/'results'/f'checkpoint_metrics_{a.split}.json').write_text(json.dumps(records,indent=2)+'\n')
if records:
    best=max(records,key=lambda x:x['map50'] if x['map50'] is not None else -1)
    (ROOT/'results'/f'best_checkpoint_{a.split}.json').write_text(json.dumps(best,indent=2)+'\n')
    if a.split=='val' and not a.no_copy_best:
        destination=ROOT/'runs/train/backup/yolov4-bee_best.weights'
        shutil.copy2(best['weight'],destination)
        best['copied_to']=str(destination)
        (ROOT/'results/best_checkpoint_val.json').write_text(json.dumps(best,indent=2)+'\n')
    print('BEST',best)
