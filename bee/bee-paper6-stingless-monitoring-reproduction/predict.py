#!/usr/bin/env python3
from pathlib import Path
import argparse,json,cv2
from darknet_detector import DarknetDetector
ROOT=Path(__file__).resolve().parent
p=argparse.ArgumentParser(); p.add_argument('source',type=Path); p.add_argument('--weights',type=Path,default=ROOT/'runs/train/backup/yolov3-tiny-bee_final.weights'); p.add_argument('--output',type=Path,default=ROOT/'runs/predictions'); a=p.parse_args(); a.output.mkdir(parents=True,exist_ok=True)
det=DarknetDetector(a.weights); images=[a.source] if a.source.is_file() else sorted(a.source.glob('*.*')); records=[]
for src in images:
 im=cv2.imread(str(src))
 if im is None: continue
 ds=det.predict(im)
 for b,c in ds:
  x,y,w,h=map(int,b); cv2.rectangle(im,(x,y),(x+w,y+h),(0,255,0),2); cv2.putText(im,f'bee {c:.2f}',(x,max(15,y-3)),0,.45,(0,255,0),1)
 cv2.imwrite(str(a.output/src.name),im); records.append({'image':str(src),'detections':len(ds)})
det.close(); (a.output/'predictions.json').write_text(json.dumps(records,indent=2)); print(json.dumps(records,indent=2))

