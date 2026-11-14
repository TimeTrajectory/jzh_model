#!/usr/bin/env python3
"""Launch or resume the exact Darknet YOLOv4 training command."""
from pathlib import Path
import argparse, subprocess

ROOT=Path(__file__).resolve().parent
ap=argparse.ArgumentParser(); ap.add_argument('--resume',type=Path); ap.add_argument('--map',action='store_true')
a=ap.parse_args()
cmd=[str(ROOT/'vendor/darknet/darknet'),'detector','train',str(ROOT/'data/bee22_darknet/bee.data'),str(ROOT/'configs/yolov4-bee.cfg'),str((a.resume or ROOT/'weights/yolov4.conv.137').resolve()),'-dont_show','-clear']
if a.resume: cmd.remove('-clear')
if a.map: cmd.append('-map')
print(' '.join(cmd)); subprocess.run(cmd,cwd=ROOT,check=True)
