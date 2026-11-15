#!/usr/bin/env python3
"""Train or resume the fixed Darknet YOLOv3-tiny detector."""
from pathlib import Path
import argparse,subprocess
ROOT=Path(__file__).resolve().parent
p=argparse.ArgumentParser(); p.add_argument('--resume',type=Path); a=p.parse_args()
weight=(a.resume or ROOT/'weights/yolov3-tiny.conv.15').resolve()
cmd=[str(ROOT/'vendor/darknet/darknet'),'detector','train',str(ROOT/'data/bee22_darknet/bee.data'),str(ROOT/'configs/yolov3-tiny-bee.cfg'),str(weight),'-dont_show']
if not a.resume: cmd.append('-clear')
print(' '.join(cmd)); subprocess.run(cmd,cwd=ROOT,check=True)

