#!/usr/bin/env python3
"""Render MOT-format result files on a BEE22 sequence."""
from pathlib import Path
from collections import defaultdict
import argparse,csv,cv2
ROOT=Path(__file__).resolve().parent; SOURCE=ROOT.parent/'bee-paper2-tracking-reproduction'/'data'/'BEE22'/'test'
p=argparse.ArgumentParser(); p.add_argument('--sequence',default='BEE22-12'); p.add_argument('--tracking-dir',type=Path,default=ROOT/'runs/tracking'); p.add_argument('--output',type=Path); a=p.parse_args()
by_frame=defaultdict(list)
with (a.tracking_dir/f'{a.sequence}.txt').open() as f:
    for r in csv.reader(f): by_frame[int(r[0])].append((int(r[1]),*map(float,r[2:6])))
images=sorted((SOURCE/a.sequence/'img1').glob('*.jpg')); first=cv2.imread(str(images[0])); h,w=first.shape[:2]; out=a.output or a.tracking_dir/f'{a.sequence}_tracked.mp4'; writer=cv2.VideoWriter(str(out),cv2.VideoWriter_fourcc(*'mp4v'),25,(w,h))
for path in images:
    im=cv2.imread(str(path))
    for ident,x,y,bw,bh in by_frame[int(path.stem)]:
        color=((ident*37)%200+55,(ident*83)%200+55,(ident*129)%200+55); cv2.rectangle(im,(int(x),int(y)),(int(x+bw),int(y+bh)),color,2); cv2.putText(im,str(ident),(int(x),max(12,int(y)-3)),cv2.FONT_HERSHEY_SIMPLEX,.5,color,1)
    writer.write(im)
writer.release(); print(out)
