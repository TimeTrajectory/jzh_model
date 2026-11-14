#!/usr/bin/env python3
"""Download pinned Darknet and official YOLOv4 convolutional initialization."""
from pathlib import Path
import hashlib, subprocess

ROOT=Path(__file__).resolve().parent
DARKNET_COMMIT="59596d7880f6504768df41d6daa586f5cb2b932f"
URL="https://github.com/AlexeyAB/darknet/releases/download/yolov4/yolov4.conv.137"

def main():
    vendor=ROOT/'vendor'/'darknet'
    if not vendor.exists():
        subprocess.run(['git','clone','https://github.com/AlexeyAB/darknet.git',str(vendor)],check=True)
    subprocess.run(['git','-C',str(vendor),'fetch','--depth','1','origin',DARKNET_COMMIT],check=True)
    subprocess.run(['git','-C',str(vendor),'checkout','--detach',DARKNET_COMMIT],check=True)
    out=ROOT/'weights'/'yolov4.conv.137'; out.parent.mkdir(exist_ok=True)
    if not out.exists() or out.stat().st_size != 170_038_676:
        subprocess.run([str(ROOT/'.venv/bin/python'),str(ROOT/'download_weights_parallel.py')],check=True)
    print(out, out.stat().st_size, hashlib.sha256(out.read_bytes()).hexdigest())
if __name__=='__main__': main()
