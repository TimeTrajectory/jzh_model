"""Render BEE22 MOT-format tracking output onto the source frames."""
from __future__ import annotations
import argparse
import csv
from collections import defaultdict
from pathlib import Path
import cv2

ROOT = Path(__file__).resolve().parent
p = argparse.ArgumentParser()
p.add_argument('--sequence', default='BEE22-12')
p.add_argument('--tracking-dir', type=Path, default=ROOT / 'runs/tracking')
p.add_argument('--output', type=Path)
a = p.parse_args()
frames = defaultdict(list)
with (a.tracking_dir / f'{a.sequence}.txt').open() as f:
    for row in csv.reader(f):
        frame, identity = int(row[0]), int(row[1])
        x, y, w, h = map(float, row[2:6])
        frames[frame].append((identity, int(x), int(y), int(w), int(h)))
images = sorted((ROOT / 'data/BEE22/test' / a.sequence / 'img1').glob('*.jpg'))
if not images: raise FileNotFoundError(a.sequence)
first = cv2.imread(str(images[0])); height, width = first.shape[:2]
out = a.output or ROOT / 'runs/tracking' / f'{a.sequence}_tracked.mp4'
out.parent.mkdir(parents=True, exist_ok=True)
writer = cv2.VideoWriter(str(out), cv2.VideoWriter_fourcc(*'mp4v'), 25, (width, height))
if not writer.isOpened(): raise RuntimeError(f'Cannot write {out}')
for image in images:
    canvas = cv2.imread(str(image))
    for identity, x, y, w, h in frames[int(image.stem)]:
        color = (int((identity * 37) % 200 + 55), int((identity * 83) % 200 + 55), int((identity * 129) % 200 + 55))
        cv2.rectangle(canvas, (x,y), (x+w,y+h), color, 2)
        cv2.putText(canvas, str(identity), (x, max(y-4, 12)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
    writer.write(canvas)
writer.release()
print(out)
