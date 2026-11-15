#!/usr/bin/env python3
"""Run the fixed post-training protocol and rebuild all reports."""
from pathlib import Path
import subprocess
ROOT=Path(__file__).resolve().parent; PY=ROOT/'.venv/bin/python'; W=ROOT/'runs/train/backup/yolov3-tiny-bee_final.weights'
def run(*args):
 cmd=[str(PY),*map(str,args)]; print('+',' '.join(cmd),flush=True); subprocess.run(cmd,cwd=ROOT,check=True)
if not W.exists(): raise SystemExit(f'missing final weights: {W}')
run(ROOT/'collect_results.py'); run(ROOT/'evaluate_detector.py','--weights',W,'--split','val'); run(ROOT/'evaluate_detector.py','--weights',W,'--split','test'); run(ROOT/'condition_experiment.py','--weights',W,'--samples','20'); run(ROOT/'update_results.py'); run(ROOT/'generate_documents.py')
print('Finalization complete.')

