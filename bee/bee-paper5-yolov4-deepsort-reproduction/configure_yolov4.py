#!/usr/bin/env python3
"""Generate the one-class YOLOv4 config used by this reproduction."""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent
src = ROOT / "vendor" / "darknet" / "cfg" / "yolov4-custom.cfg"
dst = ROOT / "configs" / "yolov4-bee.cfg"
text = src.read_text()
text = re.sub(r"(?m)^batch=\d+", "batch=64", text, count=1)
text = re.sub(r"(?m)^subdivisions=\d+", "subdivisions=16", text, count=1)
text = re.sub(r"(?m)^width=\d+", "width=608", text, count=1)
text = re.sub(r"(?m)^height=\d+", "height=608", text, count=1)
text = re.sub(r"(?m)^max_batches\s*=.*$", "max_batches=6000", text, count=1)
text = re.sub(r"(?m)^steps=.*$", "steps=4800,5400", text, count=1)
text = re.sub(r"(?m)^classes=\d+", "classes=1", text)
text = re.sub(r"(?m)^mosaic=\d+", "mosaic=0", text)
lines = text.splitlines()
for i, line in enumerate(lines):
    if line.strip() == "[yolo]":
        for j in range(i - 1, -1, -1):
            if lines[j].startswith("filters="):
                lines[j] = "filters=18"; break
dst.parent.mkdir(parents=True, exist_ok=True)
dst.write_text("\n".join(lines)+"\n")
print(dst)
