#!/usr/bin/env python3
"""Predict bees in an image or directory with trained YOLOv4 weights."""
from pathlib import Path
import argparse,json,cv2
from darknet_detector import DarknetDetector

ROOT=Path(__file__).resolve().parent
p=argparse.ArgumentParser(); p.add_argument('source',type=Path); p.add_argument('--weights',type=Path,default=ROOT/'runs/train/backup/yolov4-bee_best.weights'); p.add_argument('--conf',type=float,default=.25); p.add_argument('--output',type=Path,default=ROOT/'runs/predict')
a=p.parse_args(); a.output.mkdir(parents=True,exist_ok=True); det=DarknetDetector(a.weights,a.conf)
paths=[a.source] if a.source.is_file() else sorted(x for x in a.source.rglob('*') if x.suffix.lower() in {'.jpg','.jpeg','.png'})
summary=[]
for path in paths:
    im=cv2.imread(str(path)); boxes=det.predict(im)
    for (x,y,w,h),score in boxes:
        cv2.rectangle(im,(int(x),int(y)),(int(x+w),int(y+h)),(0,200,255),2); cv2.putText(im,f'bee {score:.2f}',(int(x),max(15,int(y)-4)),cv2.FONT_HERSHEY_SIMPLEX,.5,(0,200,255),1)
    out=a.output/path.name; cv2.imwrite(str(out),im); summary.append({'source':str(path),'output':str(out),'bees':len(boxes)})
det.close(); (a.output/'summary.json').write_text(json.dumps(summary,indent=2)+'\n'); print(json.dumps(summary,indent=2))
