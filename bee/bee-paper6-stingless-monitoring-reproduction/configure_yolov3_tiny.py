#!/usr/bin/env python3
"""Generate the fixed one-class YOLOv3-tiny configuration."""
from pathlib import Path
import re
ROOT=Path(__file__).resolve().parent
src=ROOT/'vendor/darknet/cfg/yolov3-tiny.cfg'; out=ROOT/'configs/yolov3-tiny-bee.cfg'
text=src.read_text()
text=re.sub(r'^batch=1$', 'batch=64', text, flags=re.M)
text=re.sub(r'^subdivisions=1$', 'subdivisions=16', text, flags=re.M)
text=re.sub(r'^width=416$', 'width=416', text, flags=re.M); text=re.sub(r'^height=416$', 'height=416', text, flags=re.M)
text=re.sub(r'^max_batches\s*=\s*500200$', 'max_batches=2700', text, flags=re.M)
text=re.sub(r'^steps=400000,450000$', 'steps=2160,2430', text, flags=re.M)
text=re.sub(r'^classes=80$', 'classes=1', text, flags=re.M)
text=re.sub(r'^filters=255$', 'filters=18', text, flags=re.M)
text=re.sub(r'^random=1$', 'random=0', text, flags=re.M)
out.write_text(text); print(out)

