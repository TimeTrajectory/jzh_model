#!/usr/bin/env python3
"""Prepare pinned Darknet and YOLOv3-tiny convolutional initialization."""
from pathlib import Path
import hashlib, subprocess, urllib.request

ROOT=Path(__file__).resolve().parent
COMMIT='59596d7880f6504768df41d6daa586f5cb2b932f'
URL='https://raw.githubusercontent.com/hamzaMahdi/darknet/master/yolov3-tiny.conv.15'
SIZE=30_973_396
SHA256='6cec15d2ff623499a803adebf71e5334d1de5a54e00eacd32fedea01c2c8ad00'

def main():
    vendor=ROOT/'vendor/darknet'
    if not vendor.exists():
        subprocess.run(['git','clone','https://github.com/AlexeyAB/darknet.git',str(vendor)],check=True)
    subprocess.run(['git','-C',str(vendor),'fetch','--depth','1','origin',COMMIT],check=True)
    subprocess.run(['git','-C',str(vendor),'checkout','--detach',COMMIT],check=True)
    out=ROOT/'weights/yolov3-tiny.conv.15'; out.parent.mkdir(exist_ok=True)
    if not out.exists() or out.stat().st_size!=SIZE:
        tmp=out.with_suffix('.part'); req=urllib.request.Request(URL,headers={'User-Agent':'Mozilla/5.0'}); tmp.write_bytes(urllib.request.urlopen(req).read()); tmp.replace(out)
    digest=hashlib.sha256(out.read_bytes()).hexdigest()
    if digest!=SHA256: raise SystemExit(f'weight checksum mismatch: {digest}')
    print(out,out.stat().st_size,digest)
if __name__=='__main__': main()

