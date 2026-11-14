#!/usr/bin/env python3
"""Range-download the 170 MB official YOLOv4 convolutional weights."""
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
import hashlib, subprocess

ROOT=Path(__file__).resolve().parent
URL='https://downloads.sourceforge.net/project/darknet-yolo.mirror/darknet_yolo_v4_pre/yolov4.conv.137'
SIZE=170_038_676
PARTS=24
OUT=ROOT/'weights'/'yolov4.conv.137'
TMP=ROOT/'downloads'/'yolov4_parts'

def get_part(i):
    start=i*SIZE//PARTS; end=(i+1)*SIZE//PARTS-1
    path=TMP/f'{i:02d}.part'; expected=end-start+1
    if path.exists() and path.stat().st_size==expected: return i,path
    for attempt in range(10):
        proc=subprocess.run(['curl','-L','--fail','--retry','3','--silent','--show-error',
                             '-r',f'{start}-{end}','-o',str(path),URL])
        if proc.returncode==0 and path.exists() and path.stat().st_size==expected: break
    else:
        raise RuntimeError(f'part {i} failed after 10 attempts')
    if path.stat().st_size!=expected: raise RuntimeError(f'part {i}: {path.stat().st_size} != {expected}')
    return i,path

def main():
    TMP.mkdir(parents=True,exist_ok=True); OUT.parent.mkdir(exist_ok=True)
    with ThreadPoolExecutor(max_workers=PARTS) as pool:
        futures=[pool.submit(get_part,i) for i in range(PARTS)]
        for f in as_completed(futures): print('downloaded part',f.result()[0],flush=True)
    with OUT.open('wb') as dst:
        for i in range(PARTS): dst.write((TMP/f'{i:02d}.part').read_bytes())
    if OUT.stat().st_size!=SIZE: raise RuntimeError(OUT.stat().st_size)
    print(OUT,OUT.stat().st_size,hashlib.sha256(OUT.read_bytes()).hexdigest())
if __name__=='__main__': main()
