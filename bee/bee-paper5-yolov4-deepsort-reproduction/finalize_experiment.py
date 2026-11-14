#!/usr/bin/env python3
"""Run the fixed post-training protocol and regenerate all result documents."""
from pathlib import Path
import argparse, subprocess, sys

ROOT=Path(__file__).resolve().parent
PY=ROOT/'.venv/bin/python'

def run(*args):
    cmd=[str(PY),*map(str,args)]
    print('+',' '.join(cmd),flush=True)
    subprocess.run(cmd,cwd=ROOT,check=True)

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--skip-tracking',action='store_true',help='Skip the slower complete-system MOT run')
    a=p.parse_args()
    backup=ROOT/'runs/train/backup'
    candidates=[backup/'yolov4-bee_5000.weights',backup/'yolov4-bee_final.weights']
    missing=[str(x) for x in candidates if not x.exists()]
    if missing:
        raise SystemExit('Training is not complete; missing: '+', '.join(missing))
    run(ROOT/'collect_results.py')
    run(ROOT/'evaluate_checkpoints.py',*candidates)
    run(ROOT/'evaluate_detector.py','--weights',backup/'yolov4-bee_best.weights')
    if not a.skip_tracking:
        run(ROOT/'evaluate_tracking.py','--weights',backup/'yolov4-bee_best.weights')
    run(ROOT/'update_markdown_results.py')
    run(ROOT/'generate_documents.py')
    print('Finalization complete.',flush=True)

if __name__=='__main__': main()
